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
path = os.environ["sliceop_path"]

# extract year, month and day from `datetime.datetime.now()`
year = str(now.year)
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
tw = xr.open_dataset(
    path + "downloads/Twater/Twater_Longueuil_updated.nc"
    ).sel(Date=slice(start, yesterday))
# load the preprocessed data and compute a climatological seasonal cycle
tw_c = xr.open_dataset(
    path + "prepro/Twater_Longueuil_preprocessed"
    ).T_no_offset.groupby("Date.dayofyear").mean("Date").values
# offest the climatology so that it runs from
tw_c1 = tw_c[int(tw.Date[0].dt.dayofyear.values)::]
tw_c2 = tw_c[0:59]
tw_clim = np.hstack([tw_c1, tw_c2])
climtime = pd.date_range(start=datetime.datetime.strptime(year + " " + str(int(tw.Date[0].dt.dayofyear.values)), "%Y %j"),
                         end=datetime.datetime.strptime(str(int(year) + 1) + " " + str(59), "%Y %j"),
                         freq="1D")

with open(path + "auto/frozen", "r") as f:
    frozen = f.read()
f.close()
if frozen == "True":
    frozen = True
    with open(path + "auto/frozenDate", "r") as f:
        frozenDate = f.read()
    f.close()
else:
    frozen = False

xax_min = np.datetime64(year + "-07-01")
xax_max = np.datetime64(str(int(year) + 1) + "-01-31")
xticks = np.unique(pd.date_range(start=xax_min, freq="MS", periods=8).round("1D"))
xticks_diff = xticks[1] - xticks[0]
xtickmonths = [xticks[i].astype("datetime64[M]").astype(int) % 12 + 1 for i in range(0, len(xticks))]
xtickdays = [(xticks[i].astype('datetime64[D]') - xticks[i].astype('datetime64[M]') + 1).astype(int) for i in range(0, len(xticks))]

yax_min = -1
yax_max = 28

for l in ["fr_CA", "en_CA"]:
    try:
        locale.setlocale(locale.LC_TIME, l)
    except:
        pass
    xticklabels = [datetime.datetime.strptime("2000 " + f"{xtickmonths[i]:02d}" + " "
                                              + f"{xtickdays[i]:02d}", '%Y %m %d').strftime('%d %b')
                                              + "      " for i in range(0, len(xticks))]
    if l == 'fr_CA':
        climlabel = "climatologie"
        waterlabel = "observations"
        frozenlabel = "date de gel observée"
        title = "température de l'eau à Longueuil"
    elif l == 'en_CA':
        climlabel = "climatology"
        waterlabel = "observations"
        frozenlabel = "observed freeze-up"
        title = "Water temperature at Longueuil"
    fig = plt.figure(figsize=(5, 4))
    ax1 = fig.add_subplot()
    ax1.plot(climtime, tw_clim, color="gray", ls="--", label=climlabel)
    ax1.plot(tw.Date, tw.T, color="steelblue", lw=2, label=waterlabel)
    if frozen:
        ax1.vlines(np.datetime64(frozenDate), yax_min, yax_max, ls="--", color="dimgray")
        ax1.text(np.datetime64(frozenDate) + (xticks_diff/10), (yax_min + yax_max)/2, frozenlabel,
                 ha="left", va="center", rotation=90, color="dimgray", fontsize=9)
    ax1.set_xticks(xticks)
    ax1.set_xticklabels(xticklabels, rotation=45);
    ax1.tick_params(axis='x', which='major', pad=-10)
    ax1.set_ylabel(r"$^{\circ}$C")
    ax1.set_ylim(yax_min, yax_max)
    ax1.grid(linestyle="--")
    ax1.set_title(title, fontweight="bold")
    plt.legend()
    plt.subplots_adjust(left=0.15, bottom=0.2, right=0.9)
    plt.savefig(path + "auto/Twater_" + l[0:2] +" .png", dpi=300)
