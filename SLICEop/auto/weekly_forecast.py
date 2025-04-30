import os
import sys
import datetime
import numpy as np
import xarray as xr
import pandas as pd
from sklearn.linear_model import LinearRegression

now = datetime.datetime.now()
local_path = "/storage/jrieck/SLICEop/test/"

#year = str(now.year)
#month = f"{now.month:02d}"

year = os.environ["YEAR"]
month = os.environ["MONTH"]
day = os.environ["DAY"]

if month in ["01", "02", "03", "04"]:
    year = str(int(year) - 1)
elif month in ["05", "06"]:
    sys.exit("Nothing to do in May and June")

variables = ["2m_temperature", "snowfall", "total_cloud_cover"]

model = LinearRegression()

input_forecast = xr.open_dataset(local_path + "prepro/input_forecast_weekly.nc")
input_forecast_m = input_forecast.drop_vars([v for v in variables if v in input_forecast.variables])
predictors = xr.open_dataset(local_path + "prepro/monthly_predictors.nc")

predictor_frame = predictors[[v for v in variables]].to_dataframe()
predictor_frame_m = predictors.rename({v: v + "_m" for v in variables})[[v + "_m" for v in variables]].to_dataframe()
forecast_m = model.fit(predictor_frame_m, predictors.FUDoy).predict(input_forecast_m.expand_dims({"time": 1}).to_dataframe())

y = int(year)
if forecast_m[0] > 365:
    forecast_date_m = np.datetime64(str(y+1) + "-01-01") + np.timedelta64(int(np.around(forecast_m[0]-366)))
else:
    if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
        forecast_date_m = np.datetime64(str(y) + "-01-01") + np.timedelta64(int(np.around(forecast_m[0])))
    else:
        forecast_date_m = np.datetime64(str(y) + "-01-01") + np.timedelta64(int(np.around(forecast_m[0]-1)))

if os.path.isfile(local_path + "/auto/" + year + "FUDweekly"):
    with open(local_path + "/auto/" + year + "FUDweekly", "a") as f:
        #f.write("\n" + str(now)[0:10] + ",0," + str(int(np.around(forecast_m[0]))))
        f.write("\n" + year + "-" + month + "-" + day + ",0," + str(int(np.around(forecast_m[0]))))
    f.close()
else:
    with open(local_path + "/auto/" + year + "FUDweekly", "a") as f:
        #f.write("time,FUD\n" + str(now)[0:10] + ",0," + str(int(np.around(forecast_m[0]))))
        f.write("time,number,FUD\n" + year + "-" + month + "-" + day + ",0," + str(int(np.around(forecast_m[0]))))
    f.close()

if "number" in input_forecast.dims:
    for n in np.arange(0, len(input_forecast.number)):
        tmp = input_forecast.isel(number=n)
        for v in variables:
            if not v in tmp.variables:
                tmp = tmp.rename({v + "_m": v})
            if v + "_m" in tmp.variables:
                tmp = tmp.drop_vars(v + "_m")
        forecast = model.fit(predictor_frame, predictors.FUDoy).predict(tmp.expand_dims({"time": 1}).to_dataframe())
        if forecast[0] > 365:
            forecast_date = np.datetime64(str(y+1) + "-01-01") + np.timedelta64(int(np.around(forecast[0]-366)))
        else:
            if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
                forecast_date = np.datetime64(str(y) + "-01-01") + np.timedelta64(int(np.around(forecast[0])))
            else:
                forecast_date = np.datetime64(str(y) + "-01-01") + np.timedelta64(int(np.around(forecast[0]-1)))
        if os.path.isfile(local_path + "/auto/" + year + "FUDweekly"):
            with open(local_path + "/auto/" + year + "FUDweekly", "a") as f:
                #f.write("\n" + str(now)[0:10] + "," + str(n+1) + "," + str(int(np.around(forecast[0]))))
                f.write("\n" + year + "-" + month + "-" + day + "," + str(n+1) + "," + str(int(np.around(forecast[0]))))
            f.close()
        else:
            sys.exit("Output of ensemble mean forecast not written, exiting.")


with open(local_path + "/auto/forecastw", "w") as f:
    f.write(str("True"))
f.close()

print("The forecasted freezup of the St. Lawrence is " + str(forecast_date_m)
      + "\n day " + str(int(np.around(forecast_m[0]))) + " of the year")
