''' daily_prepare_data_for_echart

Needs to be run daily to update the input data to be plotted on the interactive
echart.

'''
import os
import sys
import json
import datetime
import locale
import numpy as np
import xarray as xr
import pandas as pd
from matplotlib import pyplot as plt
import cmocean.cm as cmo

# define path
now = datetime.datetime.now()
path = os.environ["sliceop_path"]

# get year and month from `datetime.now()`
thisyear = now.year
thismonth = now.month
# first year to include in echart
ymin = 1992

# define which colormap to use in echart
cmap = cmo.thermal

# load preprocessed data
tw = xr.open_dataset(
    path + "/prepro/Twater_Longueuil_preprocessed.nc"
    )
# compute climatological seasonal cycle
tw_c = tw.T_no_offset.sel(
    Date=slice(None, str(thisyear-1) + "-06-30")
    ).groupby("Date.dayofyear").mean("Date").values[0:-1]
# compute standard deviation of seasonal cycle
tw_cstd = tw.T_no_offset.sel(
    Date=slice(None, str(thisyear-1) + "-06-30")
    ).groupby("Date.dayofyear").std("Date").values[0:-1]
# compute the minimum observed for each day
tw_cmin = tw.T_no_offset.sel(
    Date=slice(None, str(thisyear-1) + "-06-30")
    ).groupby("Date.dayofyear").min("Date").values[0:-1]
# compute maximum observed for each day
tw_cmax = tw.T_no_offset.sel(
    Date=slice(None, str(thisyear-1) + "-06-30")
    ).groupby("Date.dayofyear").max("Date").values[0:-1]
# load most recent data (lower level of preprocessing)
tw_up = xr.open_dataset(path + "/downloads/Twater/Twater_Longueuil_updated.nc")
# load the observed freeze-up dates for all years
fud = xr.open_dataset(path + "/prepro/FUD_preprocessed.nc")
# shift all variables so that the axis is from July 1 to June 30
tw_c1 = tw_c[182::]
tw_c2 = tw_c[0:182]
tw_clim = np.hstack([tw_c1, tw_c2])
tw_cstd1 = tw_cstd[182::]
tw_cstd2 = tw_cstd[0:182]
tw_climstd = np.hstack([tw_cstd1, tw_cstd2])
tw_cmin1 = tw_cmin[182::]
tw_cmin2 = tw_cmin[0:182]
tw_climmin = np.hstack([tw_cmin1, tw_cmin2])
tw_cmax1 = tw_cmax[182::]
tw_cmax2 = tw_cmax[0:182]
tw_climmax = np.hstack([tw_cmax1, tw_cmax2])

# load 'frozen' to see if river is frozen or not and convert to python bool
with open(path + "/auto/frozen", "r") as f:
    frozen = f.read()
f.close()
if "True" in frozen:
    frozen = True
    with open(path + "/auto/frozenDate", "r") as f:
        frozenDate = f.read()
    f.close()
else:
    frozen = False

# from the csv output from `monthly_forecast.py` and `weekly_forecast.py`,
# extract the latest forecast
latest = {}
# depending on the month we are in, a different year will be in the name of the
# required file
if thismonth < 6:
    tyear = thisyear - 1
else:
    tyear = thisyear
# read the weekly and monthly forecast output
weeklyForecast = pd.read_csv(path + "/auto/" + str(tyear)
                             + "FUDweekly").to_xarray()
monthlyForecast = pd.read_csv(path + "/auto/" + str(tyear)
                              + "FUDmonthly").to_xarray()
# get the dates of the latest weekly and monthly forecast
latestWeekly = weeklyForecast.time[-1].values
latestMonthly = weeklyForecast.time[-1].values
# the last weekly forecast was made after the last monthly forecast, the
# weekly forecast is the used
if (np.datetime64(str(latestWeekly)) >= np.datetime64(str(latestMonthly))):
    latestFUD = weeklyForecast.where(
        ((weeklyForecast.time==latestWeekly)
         & (weeklyForecast.number==0))
        ).mean().FUD.values
    latest["latestForecastIssued"] = str(latestWeekly)[0:10]
# if last monthly forecast was made after the last weekly forecast, the
# monthly forecast is the used
else:
    latestFUD = monthlyForecast.where(
        ((monthlyForecast.time==latestMonthly)
         & (monthlyForecast.number==0))
         ).mean().FUD.values
    latest["latestForecastIssued"] = str(latestMonthly)[0:10]
# convert the latest forecasted dayofyear to a date
if latestFUD < 182:
    latest["latestForecast"] = str(
        datetime.datetime.strptime(str(tyear + 1) + " " + str(int(latestFUD)),
                                   "%Y %j")
        )[0:10]
else:
    latest["latestForecast"] = str(
        datetime.datetime.strptime(str(tyear) + " " + str(int(latestFUD)),
                                   "%Y %j")
        )[0:10]

# use a random, non-leap year to create a time axis for the plot. only the
# month and day will be used later, the year is unimportant
climtime = pd.date_range(
    start=datetime.datetime.strptime("2001 182", "%Y %j"),
    end=datetime.datetime.strptime("2002 181", "%Y %j"),
    freq="1D"
    )
# define dictionary to contain the data
sliceop_data = {}
# add the time axis
sliceop_data['date'] = [str(climtime[i])[5:10]
                        for i in np.arange(0, len(climtime))]
# add labels for each "year", e.g. "1992/1993" etc
sliceop_data['years'] = [str(i) + "/" + str(i + 1)
                         for i in np.arange(1992, thisyear)]
# add climatology
sliceop_data['clim'] = list(tw_clim)
#sliceop_data['clim'] = [[sliceop_data['date'][i], sliceop_data['clim'][i]] for i in range(0, len(sliceop_data['clim']))]
#sliceop_data['clim-std'] = list(tw_clim - tw_climstd)
#sliceop_data['clim+std'] = list(2 * tw_climstd)
# add minimum
sliceop_data['clim-std'] = list(tw_climmin)
# add maximum - minimum (needed to plot the range between minimum and maximum)
sliceop_data['clim+std'] = list(tw_climmax - tw_climmin)
#sliceop_data['clim-std'] = [[sliceop_data['date'][i], sliceop_data['clim-std'][i]] for i in range(0, len(sliceop_data['clim']))]
#sliceop_data['clim+std'] = [[sliceop_data['date'][i], sliceop_data['clim+std'][i]] for i in range(0, len(sliceop_data['clim']))]
# define dictionaries to contain the RGB colors and the freeze-up dates
colormap = {}
fuds = {}
# depending on the month we are in, a different year will be needed to define
# the colormap
if thismonth > 6:
    tyear = thisyear + 1
else:
    tyear = thisyear
# define range to read colors from colormap in the range (0.2, 0.8), avoiding
# values too close to 0 or 1 that would result in very light or dark colors and
# thus not be visible on the graph (depending on light- or dark-mode)
cpos = np.linspace(0.2, 0.8, tyear - ymin)
# extract data for each season (Jul. 1 - Jun. 30)
for y in np.arange(ymin, tyear):
    year = str(y)
    # start one day later in leap years, i.e. keeping the delta t to the last
    # day of the year the same
    if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
        ctime = pd.date_range(
            start=datetime.datetime.strptime(year + " " + str(183), "%Y %j"),
            end=datetime.datetime.strptime(str(int(year) + 1) + " " + str(181),
                                           "%Y %j"),
            freq="1D"
            )
    else:
        ctime = pd.date_range(
            start=datetime.datetime.strptime(year + " " + str(182), "%Y %j"),
            end=datetime.datetime.strptime(str(int(year) + 1) + " " + str(181),
                                           "%Y %j"),
            freq="1D"
            )
    # if we are in the current season, remove the mean offset to make the
    # recent data comparable to preprocessed data from past seasons
    if ((tyear > thisyear) | ((y==tyear-1) & (thismonth<=6))):
        # subtract the mean offset
        tw_out = (tw_up.T.sel(Date=slice(str(ctime[0]), str(ctime[-1])))
                  - tw.T_winter_offset.mean()).values
        # set negatives to 0
        tw_out[tw_out < 0] = 0
        # add missing values for future dates
        missing = 365 - len(tw_out)
        sliceop_data[str(y) + "/" + str(y + 1)] = list(
            list(tw_out) + [np.nan] * missing
            )
        #sliceop_data[str(y) + "/" + str(y + 1)] = [[sliceop_data['date'][i], sliceop_data[str(y) + "/" + str(y + 1)][i]]
        #                                           for i in range(0, len(sliceop_data[str(y) + "/" + str(y + 1)]))]
    # if we are in past seasons, add the preprocessed data to dataset
    else:
        tw_out = tw.T_no_offset.sel(Date=ctime).values
        sliceop_data[str(y) + "/" + str(y + 1)] = list(tw_out)
        #sliceop_data[str(y) + "/" + str(y + 1)] = [[sliceop_data['date'][i], sliceop_data[str(y) + "/" + str(y + 1)][i]]
        #                                           for i in range(0, len(sliceop_data[str(y) + "/" + str(y + 1)]))]
    # add either the observed or forecasted freeze-up date to the
    # time series of freeze-up dates
    if ((tyear > thisyear) | ((y==tyear-1) & (thismonth<=6))):
        if not frozen:
            fuds[str(y) + "/" + str(y+1)] = latest["latestForecast"][5:10]
        else:
            fuds[str(y) + "/" + str(y+1)] = frozenDate[5:10]
    else:
        fuds[str(y) + "/" + str(y+1)] = str(fud.FUD.values[y - ymin])[5:10]
    # add the colors from cmocean colormap to the color data
    colormap[str(y) + "/" + str(y+1)] = '#%02x%02x%02x' % tuple([
        int(cmap(cpos[y-ymin])[i] * 255) for i in [0, 1, 2]
        ])
# add climatological freeze-up date
fudoys = np.array([
    int(datetime.datetime.strptime("2001-" + fuds[i],
        "%Y-%m-%d").strftime('%j')) for i in fuds.keys()
    ])
fudoys[fudoys<182] = fudoys[fudoys<182] + 365
fuds["clim"] = str(datetime.datetime.strptime("2001 "
    + str(int(np.mean(fudoys))), "%Y %j"))[5:10]

# save data to json files
with open(path + '/echart/sliceop_data.json', 'w') as fp:
    json.dump(sliceop_data, fp)

with open(path + '/echart/colormap.json', 'w') as fp:
    json.dump(colormap, fp)

with open(path + '/echart/fuds.json', 'w') as fp:
    json.dump(fuds, fp)

with open(path + '/echart/latest.json', 'w') as fp:
    json.dump(latest, fp)

if frozen:
    with open(path + '/echart/frozen.js', 'w') as fp:
        fp.write("frozen=true")
else:
    with open(path + '/echart/frozen.js', 'w') as fp:
        fp.write("frozen=false")
