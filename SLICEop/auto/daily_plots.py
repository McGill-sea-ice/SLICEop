''' daily_plots

Plot the time series of water temperature in Longueuil each day with the
updated values from the thermistor.

'''
import os
import sys
import datetime
import locale
import numpy as np
import xarray as xr
import pandas as pd
from matplotlib import pyplot as plt

# define path
now = datetime.datetime.now()
path = os.environ["SLICEOP_PATH"]

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
# year
if now.month < 7:
    year = f"{(now.year - 1):04d}"

# define the limits of the time series to plot
# we want to plot from July 1 of 'year' until yesterday
# create a datetim64 for yesterday
yesterday = np.datetime64(
    year + "-" + month + "-" + day
    ) - np.timedelta64(1, "D")
# datetime64 of the start (July 1)
start = np.datetime64(year + "-07-01")
# load the time series of water temperature including the most recent and
# extract the required date range
twu = xr.open_dataset(
    path + "/downloads/Twater/Twater_Longueuil_updated.nc"
    ).sel(Date=slice(start, yesterday))
# load the preprocessed data
twp = xr.open_dataset(
    path + "/prepro/Twater_Longueuil_preprocessed.nc"
    )
# load observed freeze-up dates
FUD = xr.open_dataset(
    path + "/prepro/FUD_preprocessed.nc"
    )
# compute mean observed freeze-up
fud_clim = FUD.FUDoy.mean().values
if fud_clim > 365:
    fud_clim -= 365
    climfrozenDate = str(datetime.datetime.strptime("2002 " + str(int(np.around(fud_clim))), "%Y %j"))
else:
    climfrozenDate = str(datetime.datetime.strptime("2001 " + str(int(np.around(fud_clim))), "%Y %j"))
# read the weekly and monthly forecast output
if ((int(month)==7) & (int(day)<7)):
    weeklyForecast = pd.read_csv(path + "/auto/" + str(int(year)-1)
                                 + "FUDweekly").to_xarray()
    monthlyForecast = pd.read_csv(path + "/auto/" + str(int(year)-1)
                                  + "FUDmonthly").to_xarray()
else:
    monthlyForecast = pd.read_csv(path + "/auto/" + str(year)
                                  + "FUDmonthly").to_xarray()
    try:
        weeklyForecast = pd.read_csv(path + "/auto/" + str(year)
                                     + "FUDweekly").to_xarray()
    except:
        weeklyForecast = monthlyForecast
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
# if last monthly forecast was made after the last weekly forecast, the
# monthly forecast is the used
else:
    latestFUD = monthlyForecast.where(
        ((monthlyForecast.time==latestMonthly)
         & (monthlyForecast.number==0))
         ).mean().FUD.values
# convert the latest forecasted dayofyear to a date
if latestFUD < 182:
    latestForecast = "2002" + str(
        datetime.datetime.strptime(str(year + 1) + " " + str(int(np.around(latestFUD))),
                                   "%Y %j")
        )[4:10]
else:
    latestForecast = "2001" + str(
        datetime.datetime.strptime(str(year) + " " + str(int(np.around(latestFUD))),
                                   "%Y %j")
        )[4:10]
# remove mean offset from current season's data
tw = (twu.T - twp.T_winter_offset.mean().values)
# compute climatological cycle
tw_c = twp.T_no_offset.groupby("Date.dayofyear").mean("Date").values[0:-1]
# offest the climatology so that it runs from July 1 tp June 30
tw_c1 = tw_c[182::]
tw_c2 = tw_c[0:182]
tw_clim = np.hstack([tw_c1, tw_c2])
# use a random, non-leap year to create a time axis for the plot. only the
# month and day will be used later, the year is unimportant
climtime = pd.date_range(
    start=datetime.datetime.strptime("2001 182", "%Y %j"),
    end=datetime.datetime.strptime("2002 181", "%Y %j"),
    freq="1D"
    )
y = int(year)
# define the date range to extract from the time series
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
# remove the mean offset to make the
# recent data comparable to preprocessed data from past seasons
tw = (twu.T.sel(Date=slice(str(ctime[0]), str(ctime[-1])))
      - twp.T_winter_offset.mean().values)
# set negatives to 0
tw[tw < 0] = 0
# add missing values for future dates
missing = 365 - len(tw)
tw = list(list(tw) + [np.nan] * missing)

# if river is already frozen, get the date of freeze-up
with open(path + "/auto/frozen", "r") as f:
    frozen = f.read()
f.close()
if frozen == "True":
    frozen = True
    with open(path + "/auto/frozenDate", "r") as f:
        frozenDate = f.read()
    f.close()
    if frozenDate[0:4] == str(year):
        frozenDate = "2001" + frozenDate[4:10]
    elif frozenDate[0:4] == str(int(year)+1):
        frozenDate = "2002" + frozenDate[4:10]
else:
    frozen = False

# define x-axis limits of dummy time axis
xax_min = np.datetime64("2001-07-01")
xax_max = np.datetime64("2002-06-30")
# define x ticks, one every month
xticks = np.unique(pd.date_range(start=xax_min, freq="MS", periods=13).round("1D"))
xticks_diff = xticks[1] - xticks[0]
# define the month and day for each x-tick to construct the labels later 
xtickmonths = [xticks[i].astype("datetime64[M]").astype(int) % 12 + 1 for i in range(0, len(xticks))]
xtickdays = [(xticks[i].astype('datetime64[D]') - xticks[i].astype('datetime64[M]') + 1).astype(int) for i in range(0, len(xticks))]
# define min and maz of y-axis
yax_min = -1
yax_max = 28

# loop over either french or english
for l in ["fr_CA", "en_CA"]:
    try:
        locale.setlocale(locale.LC_TIME, l)
    except:
        pass
    # set xticklabels after locale has been set
    xticklabels = [datetime.datetime.strptime("2000 " + f"{xtickmonths[i]:02d}" + " "
                                              + f"{xtickdays[i]:02d}", '%Y %m %d').strftime('%d %b')
                                              + "      " for i in range(0, len(xticks))]
    # define labels depending on language
    if l == 'fr_CA':
        climlabel = "climatologie"
        waterlabel = "observations"
        frozenlabel = "date de gel observée"
        forecastlabel = "date de gel prévu"
        climfrozenlabel = "date de gel moyen"
        title = "température de l'eau à Longueuil"
    elif l == 'en_CA':
        climlabel = "climatology"
        waterlabel = "observations"
        frozenlabel = "observed freeze-up"
        forecastlabel = "forecasted freeze-up"
        climfrozenlabel = "climatological freeze-up"
        title = "Water temperature at Longueuil"
    # setup figure
    fig = plt.figure(figsize=(5, 4))
    ax1 = fig.add_subplot()
    # plot climatology and recent observations
    ax1.plot(climtime, tw_clim, color="gray", ls="--", label=climlabel)
    ax1.plot(climtime, tw, color="steelblue", lw=2, label=waterlabel)
    # add climatological freeze-up date
    ax1.vlines(np.datetime64(climfrozenDate), yax_min, yax_max, ls="--", lw=0.5, color="dimgray")
    ax1.text(np.datetime64(climfrozenDate) - (xticks_diff/3), (yax_min + yax_max)/1.33, climfrozenlabel,
             ha="left", va="center", rotation=90, color="dimgray", fontsize=7)
    # if river is frozen, add the freeze-up date as vertical line
    if frozen:
        ax1.vlines(np.datetime64(frozenDate), yax_min, yax_max, ls="--", color="firebrick")
        ax1.text(np.datetime64(frozenDate) + (xticks_diff/10), (yax_min + yax_max)/2, frozenlabel,
                 ha="left", va="center", rotation=90, color="firebrick", fontsize=9)
    # if not frozen, plot the forecasted freeze-up if available
    else:
        if ((int(month)==7) & (int(day)<7)):
            pass
        else:
            ax1.vlines(np.datetime64(latestForecast), yax_min, yax_max, ls="--", color="darkorange")
            ax1.text(np.datetime64(latestForecast) + (xticks_diff/10), (yax_min + yax_max)/2, forecastlabel,
                     ha="left", va="center", rotation=90, color="darkorange", fontsize=9)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels, rotation=45);
    ax1.tick_params(axis='x', which='major', pad=-10)
    ax1.set_ylabel(r"$^{\circ}$C")
    ax1.set_ylim(yax_min, yax_max)
    ax1.grid(linestyle="--")
    ax1.text(xax_min + (xticks_diff*1.2), yax_min+1, year, ha="right", va="bottom", color="k",
             fontsize=12, bbox=dict(facecolor='white', edgecolor='None', alpha=0.7))
    ax1.text(xax_max - (xticks_diff*1.2), yax_min+1, str(int(year) + 1), ha="left", va="bottom", color="k",
             fontsize=12, bbox=dict(facecolor='white', edgecolor='None', alpha=0.7))
    ax1.set_title(title, fontweight="bold")
    plt.legend()
    plt.subplots_adjust(left=0.15, bottom=0.2, right=0.9)
    plt.savefig(path + "/auto/Twater_" + l[0:2] +".png", dpi=300)
