''' monthly_preprocess

On the 7th of each month, update the monthly predictors that serve as input to
the forecast with either the new SEAS5.1 seasonal forecast issued on the 1st of
this month or, if available, the respective data from ERA5. Then compute either
the mean or the sum over the month from the hourly raw data.

'''
import os
import sys
import datetime
import numpy as np
import xarray as xr

# define path
now = datetime.datetime.now()
path = os.environ["sliceop_path"]

# if running TEST, take year, month from environment variables
# otherwise extract year, month from `datetime.datetime.now
if os.environ["TEST"]=="True":
    year = os.environ["YEAR"]
    month = os.environ["MONTH"]
else:
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"

# the "year" of the forecast remains the same even if we switch into the next
# year's Jan., Feb., Mar., Apr.
if month in ["01", "02", "03", "04"]:
    year = str(int(year) - 1)
elif month in ["05", "06"]:
    sys.exit("Nothing to do in May and June")

# define the names of the variables to preprocess as well as which month to
# use for each variable and which method to apply
variables = ["2m_temperature", "snowfall", "total_cloud_cover"]
short_vars = ["t2m", "sf", "tcc"]
months = ["12", "11", "09"]
lmonth = ["31", "30", "30"]
method = ["mean", "sum", "mean"]

# initialize dataset
monthly_vars = xr.Dataset()

for v in range(0, len(variables)):
    # define filenames to load
    era5name = str(path + "/downloads/ERA5/ERA5_" + year + months[v] + "_"
                   + variables[v] +  ".grib")
    if int(months[v]) < int(month):
        seas51name = str(path + "/downloads/SEAS51/SEAS51_" + year + months[v]
                         + "_" + variables[v] + ".grib")
    else:
        seas51name = str(path + "/downloads/SEAS51/SEAS51_" + year + month + "_"
                         + variables[v] + ".grib")
    # always use ERA5 data if it is available
    if os.path.isfile(era5name):
        print("using " + variables[v] + " from ERA5")
        era5 = xr.open_dataset(era5name, engine="cfgrib",
                               decode_timedelta=True,
                               backend_kwargs={"indexpath": ""})
        # handle old and new ECMWF ERA5 time dimension format
        if era5.step.size > 1:
            era5 = era5.rename({
                "time": "old_time"
                }).stack(time=(
                "old_time", "step"
                )).reset_index(
                ["old_time", "step"]
                ).drop_vars([
                "old_time", "step"
                ])
            era5["time"] = era5["valid_time"]
            era5 = era5.drop_vars(["valid_time"])
        else:
            era5 = era5.drop_vars(["step"])
            era5["time"] = era5["valid_time"]
            era5 = era5.drop_vars(["valid_time"])
        # transform tempertaure to Celsius
        if ((short_vars[v] == "t2m") & (era5[short_vars[v]].units == "K")):
            era5[short_vars[v]] = era5[short_vars[v]] - 273.15
        # sum over month if method is "sum"
        if method[v] == "sum":
            era5["time"] = era5["time"] - np.timedelta64(30, "m")
            tmp = era5.groupby(
                "time.month"
                ).sum(
                "time"
                ).mean(
                ("longitude", "latitude")
                )[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v] + "_m"] = tmp.drop_vars(
                [d for d in tmp.coords]
                )
        # compute monthly mean if method is "mean"
        elif method[v] == "mean":
            tmp = era5.groupby(
                "time.month"
                ).mean(
                ("time", "longitude", "latitude")
                )[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v] + "_m"] = tmp.drop_vars(
                [d for d in tmp.coords]
                )
        else:
            sys.exit("No method (sum or mean) specified")
    # use SEAS5.1 data if ERA5 is not available
    elif ((os.path.isfile(seas51name)) & (not (os.path.isfile(era5name)))):
        print("using " + variables[v] + " from SEAS5.1")
        seas51 = xr.open_dataset(seas51name, engine="cfgrib",
                                 decode_timedelta=True,
                                 backend_kwargs={"indexpath": ""})
        # handle old and new ECMWF ERA5 time dimension format
        if seas51.time.size == 1:
            seas51 = seas51.drop_vars("time").rename({"valid_time": "time"})
        # transform tempertaure to Celsius
        if ((short_vars[v] == "t2m") & (seas51[short_vars[v]].units == "K")):
            seas51[short_vars[v]] = seas51[short_vars[v]] - 273.15
        # sum over month if method is "sum"
        if method[v] == "sum":
            seas51 = seas51.set_coords("time")
            seas51 = seas51.set_xindex("time")
            tmp = seas51.mean(
            ("longitude", "latitude")
            )[short_vars[v]].sel(
            time=year + "-" + months[v] + "-" + lmonth[v], method="nearest"
            )
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        # compute monthly mean if method is "mean"
        elif method[v] == "mean":
            tmp = seas51.groupby("time.month").mean(
            ("step", "longitude", "latitude")
            )[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        else:
            sys.exit("No method (sum or mean) specified")
        # compute the ensemble average over all ensemble members ('number')
        monthly_vars[variables[v] + "_m"] = monthly_vars[variables[v]].mean(
            "number"
            )
    else:
        sys.exit(variables[v] + " not found")

# save data to disk
monthly_vars.to_netcdf(path + "/prepro/input_forecast.nc")

# save information on whether the preprocessing was succesful or not
with open(path + "/prepro/prepro", "w") as f:
    f.write(str("True"))
f.close()
