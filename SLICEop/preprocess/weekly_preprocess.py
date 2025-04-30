import os
import sys
import datetime
import numpy as np
import xarray as xr

now = datetime.datetime.now()
local_path = "/storage/jrieck/SLICEop/test/"

#year = str(now.year)
#month = f"{now.month:02d}"
#day = now.day

year = os.environ["YEAR"]
month = os.environ["MONTH"]
day = int(os.environ["DAY"])

if month in ["01", "02", "03", "04"]:
    year = str(int(year) - 1)
elif month in ["05", "06"]:
    sys.exit("Nothing to do in May and June")
elif month == "07":
    if day < 7:
        sys.exit("No weekly forecast before the first monthly forecast has been issued.")

variables = ["2m_temperature", "snowfall", "total_cloud_cover"]
short_vars = ["t2m", "sf", "tcc"]
months = ["12", "11", "09"]
lmonth = ["31", "30", "30"]
method = ["mean", "sum", "mean"]

monthly_vars = xr.Dataset()

for v in range(0, len(variables)):
    era5name = local_path + "downloads/ERA5/ERA5_" + year + months[v] + "_" + variables[v] +  ".grib"
    era5partialname = local_path + "downloads/ERA5/ERA5_" + year + months[v] + "_" + variables[v] +  ".partial.grib"
    mslice = slice(year + "-" + months[v] + "-01", None)
    if int(months[v]) < int(month):
        seas51name = local_path + "downloads/SEAS51/SEAS51_" + year + months[v] + "_" + variables[v] + ".grib"
    else:
        if day < 7:
            if month == "01":
               mm1 = "12"
            else:
                mm1 = f"{(int(month) - 1):02d}"
            seas51name = local_path + "downloads/SEAS51/SEAS51_" + year + mm1 + "_" + variables[v] + ".grib"
        else:
            seas51name = local_path + "downloads/SEAS51/SEAS51_" + year + month + "_" + variables[v] + ".grib"
    if os.path.isfile(era5name):
        print("using " + variables[v] + " from ERA5")
        era5 = xr.open_dataset(era5name, engine="cfgrib", decode_timedelta=True, backend_kwargs={"indexpath": ""})
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
            tmp = era5.groupby("time.month").sum("time").mean(("longitude", "latitude"))[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        elif method[v] == "mean":
            tmp = era5.groupby("time.month").mean(("time", "longitude", "latitude"))[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        else:
            sys.exit("No method (sum or mean) specified")
        monthly_vars[variables[v] + "_m"] = monthly_vars[variables[v]]
    elif ((os.path.isfile(seas51name)) & (not (os.path.isfile(era5name)))):
        print("using " + variables[v] + " from SEAS5.1")
        seas51 = xr.open_dataset(seas51name, engine="cfgrib", decode_timedelta=True, backend_kwargs={"indexpath": ""})
        if seas51.time.size == 1:
            seas51 = seas51.drop_vars("time").rename({"valid_time": "time"})
        if ((short_vars[v] == "t2m") & (seas51[short_vars[v]].units == "K")):
            seas51[short_vars[v]] = seas51[short_vars[v]] - 273.15
        if os.path.isfile(era5partialname):
            print("updating " + variables[v] + " with ERA5 data")
            era5p = xr.open_dataset(era5partialname, engine="cfgrib", decode_timedelta=True, backend_kwargs={"indexpath": ""})
            if era5p.step.size > 1:
                era5p = era5p.rename({"time": "old_time"}).stack(time=("old_time", "step")).reset_index(["old_time", "step"]).drop_vars(["old_time", "step"])
                era5p["time"] = era5p["valid_time"]
                era5p = era5p.drop_vars(["valid_time"])
            else:
                era5p = era5p.drop_vars(["step"])
                era5p["time"] = era5p["valid_time"]
                era5p = era5p.drop_vars(["valid_time"])
            if ((short_vars[v] == "t2m") & (era5p[short_vars[v]].units == "K")):
                era5p[short_vars[v]] = era5p[short_vars[v]] - 273.15
            if method[v] == "sum":
                era5p = era5p.mean(("longitude", "latitude")).resample(time="1D").sum().sel(time=mslice)
            elif method[v] == "mean":
                era5p = era5p.mean(("longitude", "latitude")).resample(time="1D").mean().sel(time=mslice)
            seas51 = seas51.mean(("longitude", "latitude")).transpose("number", "step")
            if int(seas51.time[0].dt.month.values) >= int(era5p.time[0].dt.month.values):
                i1 = 0
                i1p = 1
                i2 = int((seas51.time == era5p.time[-1]).argmax())
                if method[v] == "sum":
                    old_sum_at_i2 = seas51[short_vars[v]][:, i2].copy().values
                    seas51[short_vars[v]][:, i1:i2+1] = era5p[short_vars[v]].cumsum("time")[i1p::].values
                    seas51[short_vars[v]][:, i2+1::] = seas51[short_vars[v]][:, i2+1::].values - old_sum_at_i2[:, None] + seas51[short_vars[v]][:, i2].values[:, None]
                elif method[v] == "mean":
                    seas51[short_vars[v]][:, i1:i2+1] = era5p[short_vars[v]][i1p::].values
            else:
                i1 = int((seas51.time == era5p.time[0]).argmax())
                i1p = 0
                i2 = int((seas51.time == era5p.time[-1]).argmax())
                if method[v] == "sum":
                    old_sum_at_i2 = seas51[short_vars[v]][:, i2].copy().values
                    seas51[short_vars[v]][:, i1:i2+1] = seas51[short_vars[v]][:, i1-1].values + era5p[short_vars[v]].cumsum("time")[i1p::].values
                    seas51[short_vars[v]][:, i2+1::] = seas51[short_vars[v]][:, i2+1::].values - old_sum_at_i2[:, None] + seas51[short_vars[v]][:, i2].values[:, None]
                elif method[v] == "mean":
                    seas51[short_vars[v]][:, i1:i2+1] = era5p[short_vars[v]][i1p::].values
        else:
            seas51 = seas51.mean(("longitude", "latitude"))
        if method[v] == "sum":
            seas51 = seas51.set_coords("time")
            seas51 = seas51.set_xindex("time")
            tmp = seas51[short_vars[v]].sel(time=year + "-" + months[v] + "-" + lmonth[v], method="nearest")
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        elif method[v] == "mean":
            tmp = seas51.groupby("time.month").mean("step")[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        else:
            sys.exit("No method (sum or mean) specified")
        monthly_vars[variables[v] + "_m"] = monthly_vars[variables[v]].mean("number")
    else:
        sys.exit(variables[v] + " not found")

monthly_vars.to_netcdf(local_path + "prepro/input_forecast_weekly.nc")

with open(local_path + "prepro/preprow", "w") as f:
    f.write(str("True"))
f.close()
