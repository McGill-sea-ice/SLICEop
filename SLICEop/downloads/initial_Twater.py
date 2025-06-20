''' initial_Twater

Due to different data format of the water temperature data from the water
treatment plant in Longueuil, some initial preprocessing and combining has to
be performed.
T_water from 1992-01-01 to 2021-12-31 is available as daily averages in a
`.csv` spreadsheet. There is currently no data available for 2022-01-01 to
2023-11-14, this gap will be filled by the 1992-2021 climatology. From
2023-11-15 to 2024-12-16 data is available in another `.csv` spreadsheet with
1-minute resolution. Starting at 2024-12-17, data is available in `.dat` text
files at 1-minute resolution, tranferred to the local server once every hour.
A few of those files on 2024-12-17 do not contain any time stamps, so they get
a special treatment: their time axis is deduced from the creation time of the
respective files. All this data is combined into one `.netcdf` file
`Twater_Longueuil_permanent.nc`.

'''
import pandas as pd
import xarray as xr
import numpy as np
import os
import time
import datetime
import csv

# define path and verify that we are on crunch (the thermistor data from the
# water treatment plant are tranferred to crunch and are only accessible there)
requiredhost=os.environ["sliceop_twater_host"]
path = os.environ["sliceop_path"]
thermistor_path = os.environ["sliceop_thermistor_path"]
myhost = os.uname()[1]
if requiredhost not in myhost:
    sys.exit("Not on " + requiredhost +
             ", water temperatures not accessible from " + myhost)

# if Twater_Longueuil_permanent.nc already exists, this script has already
# been run successfully and we do not run it again!
if os.path.isfile(path + "downloads/Twater/Twater_Longueuil_permanent.nc"):
    sys.exit(path + "downloads/Twater/Twater_Longueuil_permanent.nc already"
             + " exists, initial_Twater.py has already been executed!")

# first we load the data that was created before the automatic transmission of
# the water temperatures from the thermistor
longueuil_in = pd.read_csv(
    path + "downloads/Twater/Tw_Longueuil_updated.csv"
    ).to_xarray().set_coords("Date").isel(index=slice(None, -1))
# convert time axis and variable names for easier use
longueuil_in["Date"] = pd.DatetimeIndex(longueuil_in['Date'].values)
longueuil_in = longueuil_in.rename(
    {"T (oC)": "T"}
    ).drop_vars(["Unnamed: 0", "Unnamed: 1", "Unnamed: 2"])
tmp = longueuil_in.T
# replace bad values with NaN
replace = [np.nan if tmp[i] == 'Bad' else float(tmp[i])
           for i in range(0, len(tmp))]
longueuil_in["T"] = ("Date", replace)
# make time axis monotonically increasing and create daily averages
longueuil_in = longueuil_in.drop_vars("index").sortby("Date")
longueuil_in = longueuil_in.resample(Date="1D").mean("Date")
# we remove outliers and compute a climatological seasonal cycle
# outliers are defined as temperature changes by more than 3 degC per day
# and/or temperature > 30 degC
longueuil_smooth = longueuil_in.copy()
dTdt_ok = np.abs(
    longueuil_in["T"].ffill(dim="Date").differentiate("Date",
                                                      datetime_unit="2D")
    ) <= 6
longueuil_smooth["T"] = longueuil_in.T.where(dTdt_ok & (longueuil_in.T <= 30.),
                                             other=np.nan)
longueuil_clim = longueuil_smooth.groupby("Date.dayofyear").mean(skipna=True)
# we add the climatology for 2022-01-01 to 2023-11-14 because we do not have data for that period
extension = xr.Dataset(
    coords={"Date": pd.date_range(start="2022-01-01",
                                  end="2023-12-31",
                                  freq="1d")}
    )
twoclim = np.hstack([longueuil_clim.T.values[0:-1],
                     longueuil_clim.T.values[0:-1]])
extension["T"] = ("Date", twoclim)
longueuil_ext = xr.merge(
    [longueuil_in, extension.sel(Date=slice(None, "2023-11-14"))]
    )
# now we add thermistor data from 2023-11-15 to 2024-12-16 because this data
# has been re-transfered with correct time stamps
# we do the same converting/renaming as before
thermistor = pd.read_csv(
    path + "downloads/Twater/StationLongueuil.dat",
    sep=",", header=3, low_memory=False
    ).to_xarray()
thermistor = thermistor.rename(
    {"Unnamed: 0": "Date", "Smp.1": "T"}
    ).drop_vars(("Unnamed: 1", "Smp", "Smp.2", "Min", "Smp.3"))
thermistor = thermistor.set_coords("Date")
thermistor["Date"] = pd.DatetimeIndex(thermistor['Date'].values)
tmp = thermistor.T.data
replace = [np.nan if tmp[i] == 'Bad' else float(tmp[i])
           for i in range(0, len(tmp))]
thermistor["T"] = ("Date", replace)
thermistor = thermistor.drop_vars("index").sortby("Date")
thermistor = thermistor.sel(Date=slice("2023-11-15", "2024-12-16"))
thermistor_daily = thermistor.resample(Date="1D").mean(dim="Date")
# combine with older data
longueuil_up2thermistor = longueuil_ext.sel(
    Date=slice(None, thermistor_daily.Date.isel(Date=0))
    )
combined = xr.merge([longueuil_up2thermistor, thermistor_daily])
# need to add thermistor data from 2024-12-17 onwards (Longueuil.dat4835.dat)
# Longueuil.dat4835.dat to Longueuil.dat4844.dat do not have timestamps... so
# we add 2024-12-17 based on the creation time of the files
manu_range = np.arange(4836, 4860)
stime = time.ctime(os.path.getmtime(thermistor_path + "Longueuil.dat"
                                    + str(manu_range[0]-1) + ".dat"))
etime = time.ctime(os.path.getmtime(thermistor_path + "Longueuil.dat"
                                    + str(manu_range[-1]-1) + ".dat"))
starttime = datetime.datetime.strptime(stime, "%a %b %d %H:%M:%S %Y")
endtime = datetime.datetime.strptime(etime, "%a %b %d %H:%M:%S %Y")
start = str(str(starttime.year) + "-" + f"{starttime.month:02d}" + "-"
            + f"{starttime.day:02d}" + " " + f"{starttime.hour:02d}" + ":00:00")
end = str(str(endtime.year) + "-" + f"{endtime.month:02d}" + "-"
          + f"{endtime.day:02d}" + " " + f"{endtime.hour:02d}" + ":59:59")
tr = pd.date_range(start=start, end=end, freq="1min")
# function to read thermistor data without time stamps
def read_thermistor(path):
    tmp = pd.read_csv(path, sep=",", header=None, quoting=csv.QUOTE_NONE)
    if tmp.shape[1] == 5:
        da = tmp.to_xarray()[1]
    elif tmp.shape[1] == 6:
        da = tmp.to_xarray()[2]
    return da.rename("T")
# read in the thermistor data without time stamps and add those time stamps from
# the `pandas.date_range` `tr` that we created
t = 0
da = read_thermistor(thermistor_path + "Longueuil.dat"
                     + str(manu_range[0]) + ".dat")
da["index"] = tr[t:t+len(da.index)]
da = da.rename({"index": "Date"})
t += len(da.Date)
for i in range(manu_range[0]+1, manu_range[-1]+1):
    tmp = read_thermistor(thermistor_path + "Longueuil.dat" + str(i) + ".dat")
    tmp["index"] = tr[t:t+len(tmp.index)]
    tmp = tmp.rename({"index": "Date"})
    da = xr.concat((da, tmp), dim="Date")
    t += len(tmp.Date)

# add the data to the time series
da_2024_12_17 = da.resample(Date="1D").mean(dim="Date")
combined = xr.merge([combined, da_2024_12_17])
# This is data that won't change and requires different treatment than the data
# that follows, so we will save it to a permanent file.
# Everything that comes after 2024-12-17 is then added to this file daily and
# saved to a updated file.
combined.to_netcdf(path + "downloads/Twater/Twater_Longueuil_permanent.nc")
# The file for the updated dataset contains the same as the permanent for now.
combined.to_netcdf(path + "downloads/Twater/Twater_Longueuil_updated.nc")
# From 2024-12-18 onward thermistor data has a timestamp and we can easliy add
#it to existing files. The first to add is file number
# 4860, we save that number to the file `next.i` for the daily updating script
# to read.
with open(path + "downloads/Twater/next.i", "w") as f:
    f.write("4860")
f.close()
