import os
import sys
import datetime
import locale
import numpy as np
import xarray as xr
import pandas as pd
from matplotlib import pyplot as plt

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

# if river is already frozen, get the date of freeze-up
with open(path + "/auto/frozen", "r") as f:
    frozen = f.read()
f.close()

if frozen == "True":
    frozen = True
    with open(path + "/auto/frozenDate", "r") as f:
        frozenDate = f.read()
    f.close()
    frozenDOY = int(datetime.datetime.strptime(frozenDate,
                                               "%Y-%m-%d").strftime('%j'))
else:
    frozen = False

# the "year" of the forecast remains the same even if we switch into the next
# year
if int(month) < 7:
    year = f"{(int(year) - 1):04d}"

# define paths of forecasts
weekly_path = path + "/auto/" + year + "FUDweekly"
monthly_path = path + "/auto/" + year + "FUDmonthly"

# load forecasted freeze-up dates depending on which files are available
if os.path.isfile(weekly_path):
    FUDweekly = pd.read_csv(weekly_path, index_col=[0, 1]).to_xarray()
    FUDweekly["time"] = pd.DatetimeIndex(FUDweekly["time"].values)
if os.path.isfile(monthly_path):
    FUDmonthly = pd.read_csv(monthly_path, index_col=[0, 1]).to_xarray()
    FUDmonthly["time"] = pd.DatetimeIndex(FUDmonthly["time"].values)
# if both monthly and weekly forecasts are available, combine the data
if (os.path.isfile(monthly_path) & os.path.isfile(weekly_path)):
    FUDall = xr.concat([FUDweekly, FUDmonthly], dim="time").sortby("time")
elif (os.path.isfile(monthly_path) & (not os.path.isfile(weekly_path))):
    FUDall = FUDmonthly
else:
    sys.exit("No data found to plot.")

# load observed freeze-up date to compute climatological date
FUD = xr.open_dataset(path + "/prepro/FUD_preprocessed.nc")
frozenCLIM = int(np.around(FUD.FUDoy.mean().values))

# define the y-axis (limits, ticks, labels) of the plot
yax_min = 343
yax_max = 396
ytick_spacing = np.max(np.diff(np.linspace(yax_min+1, yax_max-2, 10, dtype=int)))
yticks = np.arange(yax_min+1, yax_max-1, ytick_spacing, dtype=int)
yticklabels = list(np.zeros(len(yticks)))
for i in range(0, len(yticks)):
    if yticks[i] > 365:
        ytickday = yticks[i] - 365
        ytickyear = "2002"
    else:
        ytickday = yticks[i]
        ytickyear = "2001"
    yticklabels[i] = datetime.datetime.strptime(ytickyear + ' ' + str(ytickday), '%Y %j').strftime('%b-%d')

# define the x-axis (limits, ticks, labels) of the plot
xax_min = np.datetime64(year + "-07-01")
xax_max = np.datetime64(str(int(year) + 1) + "-01-31")
xticks = np.unique(pd.date_range(start=xax_min, freq="MS", periods=8).round("1D"))
if len(xticks) > 1:
    xticks_diff = xticks[1] - xticks[0]
else:
    xticks_diff = None
xtickmonths = [xticks[i].astype("datetime64[M]").astype(int) % 12 + 1 for i in range(0, len(xticks))]
xtickdays = [(xticks[i].astype('datetime64[D]') - xticks[i].astype('datetime64[M]') + 1).astype(int) for i in range(0, len(xticks))]

# loop over either french or english
for l in ["fr_CA", "en_CA"]:
    try:
        locale.setlocale(locale.LC_TIME, l)
    except:
        pass
    # set xticklabels after locale has been set
    xticklabels = [datetime.datetime.strptime("2001 " + f"{xtickmonths[i]:02d}" + " " + f"{xtickdays[i]:02d}", '%Y %m %d').strftime('%d %b') + "      " for i in range(0, len(xticks))]
    # define labels depending on language
    if l == 'fr_CA':
        frozenlabel = "date de gel observée"
        l1label = "prévision"
        l2label = "nouvelle prévision\nsaisonnière publiée"
        climlabel = "date de gel normale"
        xlabel = "prévision publiée"
        ylabel = "date de gel prévue"
        title = "Prévision de la date de gel"
    elif l == "en_CA":
        frozenlabel = "observed freeze-up"
        l1label = "forecast"
        l2label = "new seasonal\nforecast issued"
        climlabel = "climatological freeze-up"
        xlabel = "forecast issued"
        ylabel = "forecasted freeze-up date"
        title = "Freeze-up date forecast"
    # setup figure
    fig = plt.figure(figsize=(5, 4))
    ax1 = fig.add_subplot()
    # if river is frozen, add the freeze-up date as vertical line
    if (frozen & (xticks_diff != None)):
        frozenXpos = np.datetime64(year + "01-01") + np.timedelta64(frozenDOY, 'D')
        ax1.vlines(frozenXpos, yax_min, yax_max, ls="--", color="firebrick")
        ax1.text(frozenXpos + (xticks_diff/10), (yax_min + yax_max)/2, frozenlabel,
                 ha="left", va="center", rotation=90, color="firebrick", fontsize=9)
    # plot the individual forecast members
    for n in range(1, len(FUDall.number)):
        ax1.plot(FUDall.time, FUDall.FUD.sel(number=n), color="grey", alpha=0.5, lw=0, marker="4", ms=8, mew=1)
    for n in range(1, len(FUDmonthly.number)):
        ax1.plot(FUDmonthly.time, FUDmonthly.FUD.sel(number=n), color="dimgray", alpha=0.5, marker="4", lw=0, ms=8, mew=1)
    # plot the ensemble mean forecast
    ax1.plot(FUDall.time, FUDall.FUD.sel(number=0), color="indigo", label=l1label, lw=3)
    ax1.plot(FUDmonthly.time, FUDmonthly.FUD.sel(number=0), color="darkorange", marker="x", lw=0, ms=8, mew=3, label=l2label)
    # plot the climatological freeze-up date as a horizontal line
    ax1.hlines(frozenCLIM, xax_min, xax_max, ls="--", color="dimgray")
    ax1.text(np.datetime64(str(int(year) + 1) + "-02-08"), frozenCLIM-1, climlabel,
             ha="right", va="top", rotation=0, color="dimgray", fontsize=6)
    # set labels, limits, ticks, etc.
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel)
    ax1.set_ylim(yax_min, yax_max)
    ax1.set_yticks(yticks)
    ax1.set_yticklabels(yticklabels);
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels, rotation=45);
    ax1.tick_params(axis='x', which='major', pad=-10)
    ax1.legend(fontsize=9)
    ax1.text(0.02, 0.98, year, transform = ax1.transAxes, fontsize=18, ha="left", va="top")
    ax1.set_title(title, fontweight="bold")
    plt.subplots_adjust(left=0.2, bottom=0.2, right=0.95)
    plt.savefig(path + "/auto/forecast_" + l[0:2] + ".png", dpi=300)
