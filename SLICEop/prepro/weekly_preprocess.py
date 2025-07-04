''' weekly_preprocess

Each Monday, update the monthly predictors that serve as input to
the forecast with new ERA5 data that gets released over the course of the
month. If no new ERA5 data is available, use the already existing SEAS5.1
and/or ERA5 data. Then compute either the mean or the sum over the month from
the hourly raw data as for the monthly forecast.

'''
import os
import sys
import datetime
import numpy as np
import xarray as xr

# define path
now = datetime.datetime.now()
path = os.environ["SLICEOP_PATH"]

# if running TEST, take year, month, day from environment variables
# otherwise extract year, month, day from `datetime.datetime.now
if os.environ["TEST"]=="True":
    year = os.environ["YEAR"]
    month = os.environ["MONTH"]
    day = int(os.environ["DAY"])
else:
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"
    day = int(now.day)

# the "year" of the forecast remains the same even if we switch into the next
# year's Jan., Feb., Mar., Apr.
if month in ["01", "02", "03", "04"]:
    year = str(int(year) - 1)
elif month in ["05", "06"]:
    sys.exit("Nothing to do in May and June")
elif month == "07":
    if day < 7:
        sys.exit("No weekly forecast before the first monthly forecast has"
                 + " been issued.")

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
    era5partialname = str(path + "/downloads/ERA5/ERA5_" + year + months[v]
                          + "_" + variables[v] +  ".partial.grib")
    mslice = slice(year + "-" + months[v] + "-01", None)
    if int(months[v]) < int(month):
        seas51name = str(path + "/downloads/SEAS51/SEAS51_" + year + months[v]
                         + "_" + variables[v] + ".grib")
    else:
        if day < 7:
            if month == "01":
                mm1 = "12"
            else:
                mm1 = f"{(int(month) - 1):02d}"
            seas51name = str(path + "/downloads/SEAS51/SEAS51_" + year + mm1
                             + "_" + variables[v] + ".grib")
        else:
            seas51name = str(path + "/downloads/SEAS51/SEAS51_" + year + month
                             + "_" + variables[v] + ".grib")
    # if the full month is available from ERA5, always use that
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
                ).drop_vars(
                ["old_time", "step"]
                )
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
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        # compute monthly mean if method is "mean"
        elif method[v] == "mean":
            tmp = era5.groupby(
            "time.month"
            ).mean(
            ("time", "longitude", "latitude")
            )[short_vars[v]].sel(month=int(months[v]))
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        else:
            sys.exit("No method (sum or mean) specified")
        monthly_vars[variables[v] + "_m"] = monthly_vars[variables[v]]
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
        # if ERA5 data is partially available for the month, update the SEAS5.1
        # with the available ERA5 data and then compute the monthly mean/sum
        if os.path.isfile(era5partialname):
            print("updating " + variables[v] + " with ERA5 data")
            era5p = xr.open_dataset(era5partialname, engine="cfgrib",
                                    decode_timedelta=True,
                                    backend_kwargs={"indexpath": ""})
            # handle old and new ECMWF ERA5 time dimension format
            if era5p.step.size > 1:
                era5p = era5p.rename(
                {"time": "old_time"}
                ).stack(time=(
                "old_time", "step"
                )).reset_index(
                ["old_time", "step"]
                ).drop_vars(["old_time", "step"])
                era5p["time"] = era5p["valid_time"]
                era5p = era5p.drop_vars(["valid_time"])
            else:
                era5p = era5p.drop_vars(["step"])
                era5p["time"] = era5p["valid_time"]
                era5p = era5p.drop_vars(["valid_time"])
            # transform tempertaure to Celsius
            if ((short_vars[v] == "t2m") & (era5p[short_vars[v]].units == "K")):
                era5p[short_vars[v]] = era5p[short_vars[v]] - 273.15
            # count number of data points per day do detect full days
            fullday = era5p.time.resample(time="1D").count()
            # compute daily sums from hourly sums if method is "sum"
            # only keep full days
            if method[v] == "sum":
                era5p = era5p.mean(
                    ("longitude", "latitude")
                    ).resample(time="1D").sum().where(fullday==24).dropna(
                        "time"
                        ).sel(time=mslice)
            # compute daily average from hourly average if method is "mean"
            elif method[v] == "mean":
                era5p = era5p.mean(
                    ("longitude", "latitude")
                    ).resample(time="1D").mean().where(fullday==24).dropna(
                        "time"
                        ).sel(time=mslice)
            seas51 = seas51.mean(
                ("longitude", "latitude")
                ).transpose("number", "step")
            # now replace SEAS5.1 with available ERA5 data and compute mean/sum.
            # different treatmeant for cases where SEAS5.1 forecast is issued
            # the same month as ERA5 because it is then missing the 1st of the
            # month (time step 1 of SEAS5.1 is the second of the month)
            if (int(seas51.time[0].dt.month.values)
                >= int(era5p.time[0].dt.month.values)):
                # define the indeces of where to replace SEA5.1 by ERA5
                i1 = 0
                i1p = 1
                i2 = int((seas51.time == era5p.time[-1]).argmax())
                # if method is "sum" we also need to change the SEAS5.1 after
                # 'i2' to add the sum of i1:i2
                if method[v] == "sum":
                    old_sum_at_i2 = seas51[short_vars[v]][:, i2].copy().values
                    # need to add dummy dimension if there is only one data
                    # point in era5p
                    if len(era5p.time) == 1:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            era5p[short_vars[v]].cumsum("time")[i1p::].values
                            )[:, None]
                    else:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            era5p[short_vars[v]].cumsum("time")[i1p::].values
                            )
                    seas51[short_vars[v]][:, i2+1::] = np.array(
                        seas51[short_vars[v]][:, i2+1::].values
                        - old_sum_at_i2[:, None]
                        + seas51[short_vars[v]][:, i2].values[:, None]
                        )
                elif method[v] == "mean":
                    if len(era5p.time) == 1:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            era5p[short_vars[v]][i1p::].values
                            )[:, None]
                    else:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            era5p[short_vars[v]][i1p::].values
                            )
            # when SEAS5.1 is issued before ERA5, the first of the month is
            # included in SEAS5.1
            else:
                # define the indeces of where to replace SEA5.1 by ERA5
                i1 = int((seas51.time == era5p.time[0]).argmax())
                i1p = 0
                i2 = int((seas51.time == era5p.time[-1]).argmax())
                # if method is "sum" we also need to change the SEAS5.1 after
                # 'i2' to add the sum of i1:i2
                if method[v] == "sum":
                    old_sum_at_i2 = seas51[short_vars[v]][:, i2].copy().values
                    if len(era5p.time) == 1:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            seas51[short_vars[v]][:, i1-1].values
                            + era5p[short_vars[v]].cumsum("time")[i1p::].values
                            )[:, None]
                    else:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            seas51[short_vars[v]][:, i1-1].values
                            + era5p[short_vars[v]].cumsum("time")[i1p::].values
                            )
                    seas51[short_vars[v]][:, i2+1::] = np.array(
                        seas51[short_vars[v]][:, i2+1::].values
                        - old_sum_at_i2[:, None]
                        + seas51[short_vars[v]][:, i2].values[:, None]
                        )
                elif method[v] == "mean":
                    if len(era5p.time) == 1:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            era5p[short_vars[v]][i1p::].values)[:, None]
                    else:
                        seas51[short_vars[v]][:, i1:i2+1] = np.array(
                            era5p[short_vars[v]][i1p::].values)
        # use SEAS5.1 if ERA5 is not available
        else:
            seas51 = seas51.mean(("longitude", "latitude"))
        # sum over month if method is "sum"
        if method[v] == "sum":
            seas51 = seas51.set_coords("time")
            seas51 = seas51.set_xindex("time")
            tmp = seas51[short_vars[v]].sel(
                time=year + "-" + months[v] + "-" + lmonth[v],
                method="nearest"
                )
            monthly_vars[variables[v]] = tmp.drop_vars([d for d in tmp.coords])
        # compute monthly mean if method is "mean"
        elif method[v] == "mean":
            tmp = seas51.groupby(
                "time.month"
                ).mean(
                "step"
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
monthly_vars.to_netcdf(path + "/prepro/input_forecast_weekly.nc")

# save information on whether the preprocessing was succesful or not
with open(path + "/prepro/preprow", "w") as f:
    f.write(str("True"))
f.close()
