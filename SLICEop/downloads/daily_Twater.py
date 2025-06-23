'''daily_Twater

Process the water temperature data from the Longueuil water treatment plant
daily. The data with a 1-minute resolution is automatically send to a server
and this script runs a quality control on this data, computes the daily average
and adds this average to the existing time series of daily-averaged water
temperature.
Additionally, this script verifies if the St. Lawrence river is frozen based
on the temperature data. If the water temperature at the treatment plant is
below 0.75 deg. Celsius, the river is assumed to be frozen.

'''
import pandas as pd
import xarray as xr
import numpy as np
import os
import time
import datetime
import csv
import sys

# path to SLICEop
path = os.environ["SLICEOP_PATH"]
thermistor_path = os.environ["SLICEOP_THERMISTOR_PATH"]

# function to read data from thermistor (works for files newer than
# Longueuil.dat4860.dat, before that the format was different)
def read_thermistor_new(inputfile):
    # read thermistor data and convert to xarray, define dimension names
    tmp = pd.read_csv(inputfile, sep=",",  header=None,
        quoting=csv.QUOTE_ALL).to_xarray().rename({0: "Date",
            2: "T"}).drop_vars((1, 3, 4, 5))
    # set Date as coordinate and add it as an index
    tmp = tmp.set_coords("Date")
    tmp["Date"] = pd.DatetimeIndex(tmp['Date'].values)
    # replace bad values with NaN
    tmpT = tmp.T.data
    replace = [np.nan if tmpT[i] == 'Bad' else float(tmpT[i])
               for i in range(0, len(tmpT))]
    tmp["T"] = ("Date", replace)
    # clean up dataset an return
    return tmp.drop_vars("index").sortby("Date")

# load existing temperature record
ds_in = xr.open_dataset(path + "/downloads/Twater/Twater_Longueuil_updated.nc")
# get lowest suffix for temperature data to be added to ds_in
with open(path + "/downloads/Twater/next.i", "rb") as f:
    lowest_i = int(f.read())
f.close()
print("Adding new data to Twater_Longueuil_updated.nc,"
      + "starting at Longueuil.dat" + str(lowest_i) + ".dat")
# make sure to only include complete days, i.e. up until yesterday, in the
# daily averages to append to the existing datset
now = np.datetime64(datetime.datetime.now())
yesterday = np.datetime64(np.datetime_as_string(now - np.timedelta64(1, "D"),
                          unit='D') + "T23:59:59")
# the last day in ds_in + 1 is the first should be the first day that is added
firstday = ds_in.Date.isel(Date=-1) + np.timedelta64(1, "D")
# compute difference between yesterday and first day to be added
# if this is 0, there is no new day to be added
tds = float((yesterday - firstday).values) / 1e9
# load data from thermistor
i = lowest_i
if tds > 0:
    # read new temperature data from thermistor
    da_update = read_thermistor_new(thermistor_path + "/Longueuil.dat"
                                    + str(i) + ".dat")
    i += 1
    # add new data until the most recent file
    while os.path.isfile(thermistor_path + "/Longueuil.dat" + str(i) + ".dat"):
        try:
            tmp = read_thermistor_new(thermistor_path + "/Longueuil.dat"
                                      + str(i) + ".dat")
        except:
            # if there is an error of some sort, we will add a NaN to the
            # time series
            tmp["Date"] = tmp["Date"] + np.timedelta64(1, "h")
            tmp["T"] = np.nan
        # do not add data from today
        if tmp.Date.isel(Date=-1) <= yesterday:
            da_update = xr.concat((da_update, tmp), dim="Date",
                                  coords="minimal", compat="override")
            i += 1
        else:
            break
    # save the last suffix added to da_update so that we can restart from there
    # the day after
    with open(path + "/downloads/Twater/next.i", "w") as f:
        f.write(str(i))
    f.close()
else:
    print("No full day of temperature data available since "
          + str(firstday.values))
    sys.exit("Exiting daily_Twater.py")

# drop duplicate values on time axis
da_update = da_update.sortby("Date").drop_duplicates(dim="Date")
# run a quick smoothing to exclude outliers before computing the daily average
update_smooth = da_update.copy()
# if the temperature changes more than 1 degree per hour, is larger than
# 30 degrees or deviates more than 3 degrees from the climatological average
# of its daym it is considered an outlier and we replace it with an
# interpolated value
dTdt_ok = np.abs(da_update["T"].ffill(dim="Date").differentiate("Date",
             datetime_unit="h")) < 1.0
update_smooth["T"] = da_update.T.where(dTdt_ok & (da_update.T < 30.),
                                       other=np.nan)
tmp = update_smooth.copy()
tmp = tmp.assign_coords(year_month_day = tmp.Date.dt.strftime("%Y-%m-%d"))
deviation = (tmp.groupby("year_month_day") -
             tmp.groupby("year_month_day").mean("Date"))
update_smooth["T"] = update_smooth.T.where(deviation.T < 3.,
                         other=np.nan).interpolate_na(dim="Date")
# compute daily average from hourly data and concatenate them to the
# existing data in ds_in
updated = xr.concat([ds_in,
    update_smooth.sortby("Date").resample(Date="1D").mean(dim="Date")],
    dim="Date", compat="override", coords="minimal")
# make sure Date is in ascending order and there are no duplicate dates
updated = updated.sortby("Date").drop_duplicates(dim="Date").compute()
# save updated dataset
ds_in.close()
updated.to_netcdf(path + "/downloads/Twater/Twater_Longueuil_updated.nc",
                  mode="w")
# save info on whether data was updated
with open(path + "/downloads/Twater/updated", "w") as f:
    f.write(str("True"))
f.close()
# check if St. Lawrence is already frozen, if it is below 0.75 deg. Celsius
# we consider it frozen
if updated.T.isel(Date=-1).values < 0.75:
    with open(path + "/auto/frozen", "r") as f:
        frozen = f.read()
    f.close()
    # if the river is frozen based on yesterdays water temperature, but it was
    # not frozen the day before, we consider yesterday as the freeze-up date and
    # write that date to a file
    if frozen == "False":
        with open(path + "/auto/frozenDate", "w") as f:
            f.write(str(updated.Date.isel(Date=-1).values)[0:10])
        f.close()
        with open(path + "/auto/frozen", "w") as f:
            f.write(str("True"))
        f.close()
