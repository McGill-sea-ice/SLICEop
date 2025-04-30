import os
import sys
import datetime
import numpy as np
import xarray as xr
import pandas as pd

now = datetime.datetime.now()
path = "/aos/home/jrieck/src/SLICEop/SLICEop/"

year = str(now.year - 1)
month = f"{now.month:02d}"

if month != "06":
    sys.exit("This script should run in June, something went wrong.")

# prepare Twater
# remove periods of constant T (unless in winter)
Tw = xr.open_dataset(path + "downloads/Twater/Twater_Longueuil_updated.nc")
Tw_processed = Tw.T.copy()

dTwdt = Tw["T"].ffill(dim="Date").differentiate("Date", datetime_unit="D")
d2Twdt2 = dTwdt.differentiate("Date", datetime_unit="D")

Tw_const = pd.Series((np.abs(dTwdt) < 0.05) * (Tw.T > 2))
for _,x in Tw_const[Tw_const].groupby((1-Tw_const).cumsum()):
    diff = x.index[-1] - x.index[0]
    if diff >= 6:
        if x.index[-1] < len(Tw_const)-1:
            Tw_processed[x.index[0]:x.index[-1]+1] = np.nan
        else:
            Tw_processed[x.index[0]::] = np.nan

# filter sharp jumps
jump = np.abs(d2Twdt2) > (np.abs(d2Twdt2).mean(skipna=True) + (d2Twdt2.std(skipna=True)))
Tw_processed[jump] = np.nan

# filter high values
Tw_mean = Tw_processed.groupby("Date.dayofyear").mean("Date", skipna=True)
Tw_std = Tw_processed.groupby("Date.dayofyear").std("Date", skipna=True)
high = np.abs(Tw_processed.groupby("Date.dayofyear") - Tw_mean) > (5 * Tw_std.mean())
Tw_processed[high] = np.nan

# set negative to 0
Tw_processed[Tw_processed < 0] = 0

# fill gaps <7 days with linear interpolation
Tw_processed = Tw_processed.interpolate_na(dim="Date", use_coordinate=True, max_gap=np.timedelta64(7, "D"), fill_value=np.nan)

# add variable with offset removed
Tw_winter = Tw_processed.copy()
Tw_winter[Tw_winter > 2] = np.nan
Tw_winter[np.abs(dTwdt) > 0.05] = np.nan
Tw_winter[np.abs(d2Twdt2) > 0.05] = np.nan

Tw_winter_mean = Tw_winter.resample(Date='QS-DEC').mean(dim="Date", skipna=True)[0::4]
Tw_winter_mean["Date"] = Tw_winter_mean.Date + np.timedelta64(45,'D')

Tw_offset = xr.zeros_like(Tw_winter) + np.nan
y_min = Tw_offset.Date.dt.year.values.min()
y_max = Tw_offset.Date.dt.year.values.max()
for y in np.arange(y_min, y_max+1):
    if y != y_min:
        Tw_offset = xr.where(((Tw_offset.Date.dt.year == y-1) & (Tw_offset.Date.dt.month == 12)),
                             Tw_winter_mean.sel(Date=str(y) + "-01-15", method="nearest").values, Tw_offset)
    Tw_offset = xr.where(((Tw_offset.Date.dt.year == y) & ((Tw_offset.Date.dt.month >= 1) & (Tw_offset.Date.dt.month <= 4))),
                         Tw_winter_mean.sel(Date=str(y) + "-01-15", method="nearest").values, Tw_offset)
Tw_offset = Tw_offset.dropna(dim="Date").interp(Date=Tw_winter.Date)

Tw_no_offset = Tw_processed - Tw_offset
Tw_no_offset[Tw_no_offset < 0] = 0

Tw["T_processed"] = Tw_processed
Tw["T_winter_offset"] = Tw_offset
Tw["T_no_offset"] = Tw_no_offset
print("saving T_water")
Tw.sel(Date=slice(None, year + "-12-31")).to_netcdf(path + "prepro/Twater_Longueuil_preprocessed.nc")

# prepare timeseries of freeze-up date
Tthresh = 0.75
Tfreezing = Tw.T_no_offset.where(Tw.T_no_offset <= 0.75, 0)
Tfreezing[Tfreezing > 0] = 1

bins = []
for y in np.arange(y_min, y_max+1):
    bins = bins + [str(y) + "-11-01"] + [str(y+1) + "-05-31"]

bins = np.array(bins, dtype='datetime64')

FUD = Tfreezing.groupby_bins("Date", bins=bins).apply(lambda da: da.idxmax(dim="Date"))[0:-1:2].rename({"Date_bins": "time"}).rename("FUD")
FUD["time"] = np.arange(y_min, y_max)
FUD = FUD.to_dataset()
doy = FUD.FUD.dt.dayofyear.values
for i in np.arange(0, y_max-y_min):
    if doy[i] < 300:
        if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
            doy[i] += 366
        else:
            doy[i] += 365
FUD["FUDoy"] = ("time", doy)
print("saving FUD")
FUD.to_netcdf(path + "prepro/FUD_preprocessed.nc")

# prepare ERA5 data
variables = ["2m_temperature", "snowfall", "total_cloud_cover"]
short_vars = ["t2m", "sf", "tcc"]
months = ["12", "11", "09"]
method = ["mean", "sum", "mean"]

monthly_predictors = xr.Dataset()

for v in range(0, len(variables)):
    try:
        era5 = xr.open_mfdataset(path + "downloads/ERA5/ERA5_????" + months[v] + "_" + variables[v] + ".grib",
                                 engine="cfgrib", decode_timedelta=True, backend_kwargs={"indexpath": ""})
    except:
        sys.exit("No ERA5 data found to load.")
    if era5.step.size > 1:
        era5 = era5.rename({"time": "old_time"}).stack(time=("old_time", "step")).reset_index(["old_time", "step"]).drop_vars(["old_time", "step"])
        era5["time"] = era5["valid_time"]
        era5 = era5.drop_vars(["valid_time"])
    else:
        era5 = era5.drop_vars(["step"])
        era5["time"] = era5["valid_time"]
        era5 = era5.drop_vars(["valid_time"])
    if ((short_vars[v] == "t2m") & (era5[short_vars[v]].units == "K")):
        era5[short_vars[v]] = era5[short_vars[v]] - 273.15
    if method[v] == "sum":
        era5["time"] = era5["time"] - np.timedelta64(30, "m")
        tmp  = era5.mean(("longitude", "latitude")).resample(time="1ME").sum("time")[short_vars[v]][1::12]
        tmp["time"] = tmp["time"].values.astype("datetime64[Y]").astype(int) + 1970
        monthly_predictors[variables[v]] = tmp
    elif method[v] == "mean":
        tmp = era5.mean(("longitude", "latitude")).resample(time="1ME").mean("time")[short_vars[v]][0::12]
        tmp["time"] = tmp["time"].values.astype("datetime64[Y]").astype(int) + 1970
        monthly_predictors[variables[v]] = tmp
    else:
        sys.exit("No method (sum or mean) specified")

# find common period of FUD and ERA5
# they should be the same but in case they are not we can still run a forecast like this
FUD_start = FUD.time.min()
FUD_end = FUD.time.max()
ERA5_start = monthly_predictors.time.min()
ERA5_end = monthly_predictors.time.max()
start = max(FUD_start, ERA5_start)
end = min(FUD_end, ERA5_end)

monthly_predictors = monthly_predictors.sel(time=slice(start, end + 1))
monthly_predictors["FUDoy"] = FUD.FUDoy.sel(time=slice(start, end + 1))
monthly_predictors.drop_vars(["number", "surface"]).to_netcdf(path + "prepro/monthly_predictors.nc")

with open(path + "prepro/preproy", "w") as f:
    f.write(str("True"))
f.close()
