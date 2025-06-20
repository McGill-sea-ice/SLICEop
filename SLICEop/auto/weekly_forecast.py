''' weekly_forecast

Each Monday, this script will be run to forecast the freeze-up
date based on the data in 'input_forecast_weekly.nc'. Whether the data in
'input_forecast_weekly.nc' is based on SEAS5.1 or ERA5 or a combination, is
determined in 'weekly_preprocess.py'. The forecast will forecast a dayofyear,
with values larger than 365 indicating a freeze-up on dayofyear-365 of the
following year

'''
import os
import sys
import datetime
import numpy as np
import xarray as xr
import pandas as pd
from sklearn.linear_model import LinearRegression

# define path
now = datetime.datetime.now()
path = os.environ["sliceop_path"]

# if running TEST, take year, month, day from environment variables
# otherwise extract year, month, day from `datetime.datetime.now
if os.environ["TEST"]=="True":
    year = os.environ["YEAR"]
    month = os.environ["MONTH"]
    day = os.environ["DAY"]
else:
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"

# the "year" of the forecast remains the same even if we switch into the next
# year's Jan., Feb., Mar., Apr.
if month in ["01", "02", "03", "04"]:
    year = str(int(year) - 1)
elif month in ["05", "06"]:
    sys.exit("Nothing to do in May and June")

# define names of variables to use for the forecast
variables = ["2m_temperature", "snowfall", "total_cloud_cover"]

# define to use linear regression as the forecast model
model = LinearRegression()

# load input data
input_forecast = xr.open_dataset(path + "/prepro/input_forecast_weekly.nc")
# for the ensemble mean forecast, only keep variables with "_m" at the end of
# the name
input_forecast_m = input_forecast.drop_vars(
    [v for v in variables if v in input_forecast.variables]
    )
# load the monthly predictors (created in 'yearly_preprocess.py')
predictors = xr.open_dataset(path + "/prepro/monthly_predictors.nc")

# convert predictors do dataframe in preparation for the forecast
predictor_frame = predictors[[v for v in variables]].to_dataframe()
# create a dataframe for the ensemble mean forecast
predictor_frame_m = predictors.rename(
    {v: v + "_m" for v in variables}
    )[[v + "_m" for v in variables]].to_dataframe()
# run the ensemble mean forecast
forecast_m = model.fit(
    predictor_frame_m, predictors.FUDoy
    ).predict(
    input_forecast_m.expand_dims({"time": 1}).to_dataframe()
    )

y = int(year)
# convert forecasted dayofyear to a date
if forecast_m[0] > 365:
    forecast_date_m = np.datetime64(
        str(y+1) + "-01-01"
        ) + np.timedelta64(
        int(np.around(forecast_m[0]-366))
        )
else:
    # taking into account leap years (for the forecast, all years are
    # considered to have 365 days, i.e. dayofyear 360 is always Dec. 26)
    if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
        forecast_date_m = np.datetime64(
            str(y) + "-01-01"
            ) + np.timedelta64(
            int(np.around(forecast_m[0]))
            )
    else:
        forecast_date_m = np.datetime64(
            str(y) + "-01-01"
            ) + np.timedelta64(
            int(np.around(forecast_m[0]-1))
            )

# write ensemble mean forecast to file. the format is
# 'date forecast is issued', 'ensemble member', 'forecasted dayofyear'
# the ensemble mean is member '0'
# forecasted freeze-up dayofyears are rounded to the nearest integer number
# if output file for the current year is already present, append
if os.path.isfile(path + "/auto/" + year + "FUDweekly"):
    with open(path + "/auto/" + year + "FUDweekly", "a") as f:
        f.write("\n" + year + "-" + month + "-" + day + ",0,"
                + str(int(np.around(forecast_m[0]))))
    f.close()
# if output file is not present, create it and add header line
else:
    with open(path + "/auto/" + year + "FUDweekly", "a") as f:
        f.write("time,number,FUD\n" + year + "-" + month + "-" + day + ",0,"
                + str(int(np.around(forecast_m[0]))))
    f.close()

# if the input data contains several ensemble members, run the forecast for
# each of the members
if "number" in input_forecast.dims:
    # loop over members
    for n in np.arange(0, len(input_forecast.number)):
        tmp = input_forecast.isel(number=n)
        # if not all of the variables are available from each ensemble member,
        # use the ensemble mean
        # this mostly applies to ERA5 data, which has no ensemble members and
        # the data is treated as "ensemble mean"
        for v in variables:
            if not v in tmp.variables:
                tmp = tmp.rename({v + "_m": v})
            if v + "_m" in tmp.variables:
                tmp = tmp.drop_vars(v + "_m")
        # run the forecast
        forecast = model.fit(
            predictor_frame, predictors.FUDoy
            ).predict(
            tmp.expand_dims({"time": 1}).to_dataframe()
            )
        # convert forecasted dayofyear to a date
        if forecast[0] > 365:
            forecast_date = np.datetime64(
                str(y+1) + "-01-01"
                ) + np.timedelta64(
                int(np.around(forecast[0]-366))
                )
        # taking into account leap years (for the forecast, all years are
        # considered to have 365 days, i.e. dayofyear 360 is always Dec. 26)
        else:
            if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
                forecast_date = np.datetime64(
                    str(y) + "-01-01"
                    ) + np.timedelta64(
                    int(np.around(forecast[0]))
                    )
            else:
                forecast_date = np.datetime64(
                    str(y) + "-01-01"
                    ) + np.timedelta64(
                    int(np.around(forecast[0]-1))
                    )
        # write each members forecast to file. the format is
        # 'date forecast is issued', 'ensemble member', 'forecasted dayofyear'
        # forecasted freeze-up dayofyears are rounded to the nearest
        # integer number
        # if output file for the current year is already present, append
        if os.path.isfile(path + "/auto/" + year + "FUDweekly"):
            with open(path + "/auto/" + year + "FUDweekly", "a") as f:
                f.write("\n" + year + "-" + month + "-" + day + ","
                        + str(n+1) + "," + str(int(np.around(forecast[0]))))
            f.close()
        # do not write the ensemble members if the ensemble mean didn't work
        # something went wrong
        else:
            sys.exit("Output of ensemble mean forecast not written, exiting.")

# save information on whether the forecast was succesful or not
with open(path + "/auto/forecastw", "w") as f:
    f.write(str("True"))
f.close()

print("The forecasted freezup of the St. Lawrence is " + str(forecast_date_m)
      + "\n day " + str(int(np.around(forecast_m[0]))) + " of the year")
