''' yearly_preprocess

Once a year in June, update the time series of the predictors and the
freeze-up date with the values from the last winter season.

'''
import os
import sys
import datetime
import numpy as np
import xarray as xr
import pandas as pd

# define path
now = datetime.datetime.now()
path = os.environ["SLICEOP_PATH"]

# if running TEST, take year, month from environment variables
# otherwise extract year, month from `datetime.datetime.now
if os.environ["TEST"]=="True":
    year = os.environ["YEAR"]
    month = os.environ["MONTH"]
else:
    year = f"{(now.year - 1):04d}"
    month = f"{now.month:02d}"

# exit if the month is not June, this script should only run in June!
if month != "06":
    sys.exit("This script should run in June, something went wrong.")

#### water temperature Tw
### remove periods of constant T (unless T is near the freezing point)
# load daily average water temperature data
Tw = xr.open_dataset(path + "/downloads/Twater/Twater_Longueuil_updated.nc")
Tw_processed = Tw.T.copy()
# compute dT / dt
dTwdt = Tw["T"].ffill(dim="Date").differentiate("Date", datetime_unit="2D")
d2Twdt2 = dTwdt.differentiate("Date", datetime_unit="2D")
# if dT / dt stays below 0.1 degrees / day for at least 7 days AND T is
# greater than 2 degrees, replace T by NaN
Tw_const = pd.Series((np.abs(dTwdt) < 0.1) * (Tw.T > 2))
for _,x in Tw_const[Tw_const].groupby((1-Tw_const).cumsum()):
    diff = x.index[-1] - x.index[0]
    if diff >= 6:
        if x.index[-1] < len(Tw_const)-1:
            Tw_processed[x.index[0]:x.index[-1]+1] = np.nan
        else:
            Tw_processed[x.index[0]::] = np.nan
# filter sharp jumps
jump = np.abs(d2Twdt2) > (np.abs(d2Twdt2).mean(skipna=True)
                          + (d2Twdt2.std(skipna=True)))
Tw_processed[jump] = np.nan
# filter high values: fill in NaN whenever temperature is more than
# 5 standard deviations away from the climatology
Tw_mean = Tw_processed.groupby("Date.dayofyear").mean("Date", skipna=True)
Tw_std = Tw_processed.groupby("Date.dayofyear").std("Date", skipna=True)
high = (np.abs(Tw_processed.groupby("Date.dayofyear") - Tw_mean)
        > (5 * Tw_std.mean()))
Tw_processed[high] = np.nan
# set negative to 0
Tw_processed[Tw_processed < 0] = 0
# fill gaps <7 days with linear interpolation
Tw_processed = Tw_processed.interpolate_na(dim="Date", use_coordinate=True,
                                           max_gap=np.timedelta64(7, "D"),
                                           fill_value=np.nan)
# add variable with offset removed. the offset is the temperature that the
# water from the frozen river (which should be close to 0) has when it arrives
# at the thermistor
# this offset is calculated for each winter individually as it changes every
# year
Tw_winter = Tw_processed.copy()
# use only winter data (T < 2) and only when the river is frozen: assume that
# river is frozen when T stays constant (dT / dt and d^2T / dt^2 < 0.1)
Tw_winter[Tw_winter > 2] = np.nan
Tw_winter[np.abs(dTwdt) > 0.1] = np.nan
Tw_winter[np.abs(d2Twdt2) > 0.1] = np.nan
# compute the mean over each winter season
Tw_winter_mean = Tw_winter.resample(Date='QS-DEC').mean(dim="Date",
                                                        skipna=True)[0::4]
# offest Date to be in middle of winter
Tw_winter_mean["Date"] = Tw_winter_mean.Date + np.timedelta64(45,'D')
# compute the temperature offest for each winter season
Tw_offset = xr.zeros_like(Tw_winter) + np.nan
y_min = Tw_offset.Date.dt.year.values.min()
y_max = Tw_offset.Date.dt.year.values.max()
for y in np.arange(y_min, y_max+1):
    # use December from year-1 and January+February from year ot compute winter
    # offest, unless in the first year, where only January and February are used
    if y != y_min:
        Tw_offset = xr.where(((Tw_offset.Date.dt.year == y-1) &
                              (Tw_offset.Date.dt.month == 12)),
                             Tw_winter_mean.sel(Date=str(y) + "-01-15",
                                                method="nearest").values,
                             Tw_offset)
    Tw_offset = xr.where(((Tw_offset.Date.dt.year == y) &
                          ((Tw_offset.Date.dt.month >= 1) &
                          (Tw_offset.Date.dt.month <= 4))),
                         Tw_winter_mean.sel(Date=str(y) + "-01-15",
                                            method="nearest").values, Tw_offset)
Tw_offset = Tw_offset.dropna(dim="Date").interp(Date=Tw_winter.Date)
# remove the computed offest from the temperature
Tw_no_offset = Tw_processed - Tw_offset
# set negatives to zero
Tw_no_offset[Tw_no_offset < 0] = 0
# store everything to a `netcdf` file
Tw["T_processed"] = Tw_processed
Tw["T_winter_offset"] = Tw_offset
Tw["T_no_offset"] = Tw_no_offset
print("saving T_water")
Tw.sel(Date=slice(None, year + "-12-31")).to_netcdf(path
    + "/prepro/Twater_Longueuil_preprocessed.nc")

#### freeze-up date FUD
# compute the freeze-up dates from the water temperature, the river is
# considered frozen, if the temperature drops below 0.75 degrees. This value
# was found to lead to the best correspondance with freeze-up dates from other
# sources like ice charts etc.
Tthresh = 0.75
# construct a time series thats 1 when frozen and 0 when not frozen
Tfreezing = Tw.T_no_offset.where(Tw.T_no_offset <= 0.75, 0)
Tfreezing[Tfreezing > 0] = 1
# construct bins to group the temperature into winters
bins = []
for y in np.arange(y_min, y_max+1):
    bins = bins + [str(y) + "-11-01"] + [str(y+1) + "-05-31"]
bins = np.array(bins, dtype='datetime64')
# group together data of each winter and find the index when water is first
# frozen, i.e. Tfreezing=1
FUD = Tfreezing.groupby_bins("Date", bins=bins).apply(lambda da:
    da.idxmax(dim="Date"))[0:-1:2].rename({"Date_bins": "time"}).rename("FUD")
# make a time axis for the FUD series
FUD["time"] = np.arange(y_min, y_max)
FUD = FUD.to_dataset()
# add the day-of-year to the FUD time series and take into account leap years
doy = FUD.FUD.dt.dayofyear.values
for i in np.arange(0, y_max-y_min):
    if doy[i] < 300:
        if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
            doy[i] += 366
        else:
            doy[i] += 365
FUD["FUDoy"] = ("time", doy)
# save to `netcdf` file
print("saving FUD")
FUD.to_netcdf(path + "/prepro/FUD_preprocessed.nc")

#### ERA5 data - monthly predictors
# define variable names, short names, months and which method to use to
# compute them (monthly mean or monthly integral)
variables = ["2m_temperature", "snowfall", "total_cloud_cover"]
short_vars = ["t2m", "sf", "tcc"]
months = ["12", "11", "09"]
method = ["mean", "sum", "mean"]
# initialize dataset
monthly_predictors = xr.Dataset()
# loop over the variables and
for v in range(0, len(variables)):
    # load dataset
    try:
        era5 = xr.open_mfdataset(path + "/downloads/ERA5/ERA5_????" + months[v] + "_" + variables[v] + ".grib",
                                 engine="cfgrib", decode_timedelta=True, backend_kwargs={"indexpath": ""})
    except:
        sys.exit("No ERA5 data found to load.")
    # handle different time dimension names
    if era5.step.size > 1:
        era5 = era5.rename({"time": "old_time"}).stack(time=("old_time",
            "step")).reset_index(["old_time", "step"]).drop_vars(["old_time",
                "step"])
        era5["time"] = era5["valid_time"]
        era5 = era5.drop_vars(["valid_time"])
    else:
        era5 = era5.drop_vars(["step"])
        era5["time"] = era5["valid_time"]
        era5 = era5.drop_vars(["valid_time"])
    # convert temperature to Celsius if in Kelvin
    if ((short_vars[v] == "t2m") & (era5[short_vars[v]].units == "K")):
        era5[short_vars[v]] = era5[short_vars[v]] - 273.15
    # sum all the values in the month if method is "sum"
    if method[v] == "sum":
        era5["time"] = era5["time"] - np.timedelta64(30, "m")
        tmp  = era5.mean(("longitude",
            "latitude")).resample(time="1ME").sum("time")[short_vars[v]][1::12]
        tmp["time"] = tmp["time"].values.astype(
                          "datetime64[Y]").astype(int) + 1970
        monthly_predictors[variables[v]] = tmp
    # compute monthly mean if method is "mean"
    elif method[v] == "mean":
        tmp = era5.mean(("longitude",
            "latitude")).resample(time="1ME").mean("time")[short_vars[v]][0::12]
        tmp["time"] = tmp["time"].values.astype(
                          "datetime64[Y]").astype(int) + 1970
        monthly_predictors[variables[v]] = tmp
    else:
        sys.exit("No method (sum or mean) specified")

# find common period of FUD and ERA5
# they should be the same but in case they are not we can still run a forecast
# like this
FUD_start = FUD.time.min()
FUD_end = FUD.time.max()
ERA5_start = monthly_predictors.time.min()
ERA5_end = monthly_predictors.time.max()
start = max(FUD_start, ERA5_start)
end = min(FUD_end, ERA5_end)
# combine all data into one dateset with monthly values
monthly_predictors = monthly_predictors.sel(time=slice(start, end + 1))
monthly_predictors["FUDoy"] = FUD.FUDoy.sel(time=slice(start, end + 1))
monthly_predictors.drop_vars(["number", "surface"]).to_netcdf(
    path + "/prepro/monthly_predictors.nc")
# save information on whether the preprocessing was succesful or not
with open(path + "/prepro/preproy", "w") as f:
    f.write(str("True"))
f.close()
