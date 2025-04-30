import os
import sys
import datetime
import numpy as np
import xarray as xr

now = datetime.datetime.now()
local_path = "/storage/jrieck/SLICEop/test/"

#year = str(now.year)
#month = f"{now.month:02d}"

year = os.environ["YEAR"]
month = os.environ["MONTH"]

if month in ["01", "02", "03", "04"]:
    year = str(int(year) - 1)
elif month in ["05", "06"]:
    sys.exit("Nothing to do in May and June")

variables = ["2m_temperature", "snowfall", "total_cloud_cover"]
short_vars = ["t2m", "sf", "tcc"]
months = ["12", "11", "09"]
lmonth = ["31", "30", "30"]
method = ["mean", "sum", "mean"]

monthly_vars = xr.Dataset()

for v in range(0, len(variables)):
    era5name = local_path + "downloads/ERA5/ERA5_" + year + months[v] + "_" + variables[v] +  ".grib"
    if int(months[v]) < int(month):
        seas51name = local_path + "downloads/SEAS51/SEAS51_" + year + months[v] + "_" + variables[v] + ".grib"
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
            monthly_vars[variables[v] + "_m"] = tmp.drop_vars([d for d in tmp.coords])
        elif method[v] == "mean":
            tmp = era5.groupby("time.month").mean(("time", "longitude", "latitude"))[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v] + "_m"] = tmp.drop_vars([d for d in tmp.coords])
        else:
            sys.exit("No method (sum or mean) specified")
    elif ((os.path.isfile(seas51name)) & (not (os.path.isfile(era5name)))):
        print("using " + variables[v] + " from SEAS5.1")
        seas51 = xr.open_dataset(seas51name, engine="cfgrib", decode_timedelta=True, backend_kwargs={"indexpath": ""})
        if seas51.time.size == 1:
            seas51 = seas51.drop_vars("time").rename({"valid_time": "time"})
        if ((short_vars[v] == "t2m") & (seas51[short_vars[v]].units == "K")):
            seas51[short_vars[v]] = seas51[short_vars[v]] - 273.15
        if method[v] == "sum":
            seas51 = seas51.set_coords("time")
            seas51 = seas51.set_xindex("time")
            tmp = seas51.mean(("longitude", "latitude"))[short_vars[v]].sel(time=year + "-" + months[v] + "-" + lmonth[v], method="nearest")
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        elif method[v] == "mean":
            tmp = seas51.groupby("time.month").mean(("step", "longitude", "latitude"))[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        else:
            sys.exit("No method (sum or mean) specified")
        monthly_vars[variables[v] + "_m"] = monthly_vars[variables[v]].mean("number")
    else:
        sys.exit(variables[v] + " not found")

monthly_vars.to_netcdf(local_path + "prepro/input_forecast.nc")

with open(local_path + "prepro/prepro", "w") as f:
    f.write(str("True"))
f.close()
