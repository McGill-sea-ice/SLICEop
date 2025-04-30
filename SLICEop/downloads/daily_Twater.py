import pandas as pd
import xarray as xr
import numpy as np
import os
import time
import datetime
import csv
import sys

local_path = "/aos/home/jrieck/src/SLICEop/SLICEop/"

# function to read data from thermistor (works for files newer than Longueuil.dat4860.dat)
def read_thermistor_new(path):
    tmp = pd.read_csv(path, sep=",",  header=None,
                      quoting=csv.QUOTE_ALL).to_xarray().rename({0: "Date", 2: "T"}).drop_vars((1, 3, 4, 5))
    tmp = tmp.set_coords("Date")
    tmp["Date"] = pd.DatetimeIndex(tmp['Date'].values)
    tmpT = tmp.T.data
    replace = [np.nan if tmpT[i] == 'Bad' else float(tmpT[i]) for i in range(0, len(tmpT))]
    tmp["T"] = ("Date", replace)
    return tmp.drop_vars("index").sortby("Date")

# load existing data
ds_in = xr.open_dataset(local_path + "downloads/Twater/Twater_Longueuil_updated.nc")
# get lowest index to add to data
with open(local_path + "downloads/Twater/next.i", "rb") as f:
    lowest_i = int(f.read())
f.close()
print("Adding new data to Twater_Longueuil_updated.nc, starting at Longueuil.dat" + str(lowest_i) + ".dat")
# make sure to only include complete days, i.e. up until yesterday, in the daily averages to append to the existing datset
now = np.datetime64(datetime.datetime.now())
yesterday = np.datetime64(np.datetime_as_string(now - np.timedelta64(1, "D"), unit='D') + "T23:59:59")
firstday = ds_in.Date.isel(Date=-1) + np.timedelta64(1, "D")
tds = float((yesterday - firstday).values) / 1e9
# load data from thermistor
i = lowest_i
if tds > 0:
    da_update = read_thermistor_new("/storage/thermistor/Longueuil.dat" + str(i) + ".dat")
    i += 1
    while os.path.isfile("/storage/thermistor/Longueuil.dat" + str(i) + ".dat"):
        try:
            tmp = read_thermistor_new("/storage/thermistor/Longueuil.dat" + str(i) + ".dat")
        except:
            tmp["Date"] = tmp["Date"] + np.timedelta64(1, "h")
            tmp["T"] = np.nan
        if tmp.Date.isel(Date=-1) <= yesterday:
            da_update = xr.concat((da_update, tmp), dim="Date")
            i += 1
        else:
            break
    with open(local_path + "downloads/Twater/next.i", "w") as f:
        f.write(str(i))
    f.close()
else:
    print("No full day of temperature data available since " + str(firstday.values))
    sys.exit("Exiting daily_Twater.py")

# run a quick smoothing to exclude outliers before computing the daily average
update_smooth = da_update.copy()
dTdt_ok = np.abs(da_update["T"].ffill(dim="Date").differentiate("Date", datetime_unit="h")) < 0.1
update_smooth["T"] = da_update.T.where(dTdt_ok & (da_update.T < 30.), other=np.nan)
# compute daily average from hourly data
updated = xr.merge([ds_in, update_smooth.sortby("Date").resample(Date="1D").mean(dim="Date")]).compute()
# save updated dataset
ds_in.close()
updated.to_netcdf(local_path + "downloads/Twater/Twater_Longueuil_updated.nc", mode="w")
# save info on whether data was updated
with open(local_path + "downloads/Twater/updated", "w") as f:
    f.write(str("True"))
f.close()
# check if St. Lawrence is already frozen
if updated.T.isel(Date=-1).values < 0.75:
    with open(local_path + "auto/frozen", "r") as f:
        frozen = f.read()
    f.close()
    if frozen == "False":
        with open(local_path + "auto/frozenDate", "w") as f:
            f.write(str(updated.Date.isel(Date=-1).values)[0:10])
        f.close()
        with open(local_path + "auto/frozen", "w") as f:
            f.write(str("True"))
        f.close()
