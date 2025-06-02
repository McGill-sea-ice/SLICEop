''' monthly_SEAS51_ERA5

Download the monthly predictors from either the seasonal forecast
SEAS5.1 or the reanalysis ERA5 depending on which is available. This script is
supposed to be called once a month, at the beginning of the month after the
new seasonal forecast becomes available.

'''
import os
import datetime
import cdsapi
import numpy as np

# define paths
now = datetime.datetime.now()
path = "/aos/home/jrieck/src/SLICEop/SLICEop/"
out_dir = path + "downloads/"

# extract year, month, day from `datetime.datetime.now
year = f"{now.year:04d}"
month = f"{now.month:02d}"
day = f"{(now.day - 1):02d}"

# define a function to download the ERA5 data
def download_era5(var, month, year, output_dir, lats, lons):
    # define the filename. if a file of this name is already present locally,
    # do not download it again
    filename = output_dir + "ERA5_" + str(year) + month + "_" + var + ".grib"
    if os.path.isfile(filename):
        print(filename + " is already present, no need to download")
        return
    else:
        print("Downloading " + var + " for " + str(year) + month + " from ERA5")
        try:
            client = cdsapi.Client(retry_max=5)
            client.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': ['reanalysis'],
                    'data_format': 'grib',
                    'download_format': 'unarchived',
                    'variable': [var],
                    'area': [lats[1], lons[0], lats[0], lons[1]],
                    'time': [
                        '00:00','01:00', '02:00','03:00',
                        '04:00','05:00', '06:00','07:00',
                        '08:00','09:00', '10:00','11:00',
                        '12:00','13:00', '14:00','15:00',
                        '16:00','17:00', '18:00','19:00',
                        '20:00','21:00', '22:00','23:00',
                    ],
                    'day': [
                        '01', '02', '03',
                        '04', '05', '06',
                        '07', '08', '09',
                        '10', '11', '12',
                        '13', '14', '15',
                        '16', '17', '18',
                        '19', '20', '21',
                        '22', '23', '24',
                        '25', '26', '27',
                        '28', '29', '30', '31'
                    ],
                    # API ignores cases where there are less than 31 days
                    'month': [month],
                    'year': [year]
                },
                filename)
        except Exception as e:
            print(e)
            # Delete the partially downloaded file.
            if os.path.isfile(filename):
                os.remove(filename)
    return

# define a function to download the SEAS5.1 data
def download_seas51(var, month, year, output_dir, lats, lons):
    # define the filename. if a file of this name is already present locally,
    # do not download it again
    filename = output_dir + "SEAS51_" + str(year) + month + "_" + var + ".grib"
    if os.path.isfile(filename):
        print(filename + " is already present, no need to download")
        return
    else:
        print("Downloading " + var + " for " + str(year) + month + " from SEAS5.1")
        try:
            client = cdsapi.Client(retry_max=5)
            client.retrieve(
                'seasonal-original-single-levels',
                {
                    'data_format': 'grib',
                    'download_format': 'unarchived',
                    'originating_centre': 'ecmwf',
                    'system': '51',
                    'variable': [var],
                    'area': [lats[1], lons[0], lats[0], lons[1]],
                    'day': ['01'],
                    'month': [month],
                    'year': [str(year)],
                    'leadtime_hour': [
                         '24','48','72','96',
                         '120','144','168','192','216','240',
                         '264','288','312','336','360','384',
                         '408','432','456','480','504','528',
                         '552','576','600','624','648','672',
                         '696','720','744','768','792','816',
                         '840','864','888','912','936','960',
                         '984','1008','1032','1056','1080','1104',
                         '1128','1152','1176','1200','1224','1248',
                         '1272','1296','1320','1344', '1368','1392',
                         '1416','1440','1464','1488','1512','1536',
                         '1560','1584','1608','1632','1656','1680',
                         '1704','1728','1752','1776','1800','1824',
                         '1848','1872','1896','1920','1944','1968',
                         '1992','2016','2040','2064','2088','2112',
                         '2136','2160','2184','2208','2232','2256','2280',
                         '2304','2328','2352','2376','2400','2424',
                         '2448','2472','2496','2520','2544','2568',
                         '2592','2616','2640','2664','2688','2712',
                         '2736','2760','2784','2808','2832','2856',
                         '2880','2904','2928','2952','2976','3000',
                         '3024','3048','3072','3096','3120','3144',
                         '3168','3192','3216','3240','3264','3288',
                         '3312','3336','3360','3384','3408','3432',
                         '3456','3480','3504','3528','3552','3576',
                         '3600','3624','3648','3672','3696','3720',
                         '3744','3768','3792','3816','3840','3864',
                         '3888','3912','3936','3960','3984','4008',
                         '4032','4056','4080','4104','4128','4152',
                         '4176','4200','4224','4248','4272','4296',
                         '4320','4344','4368','4392','4416','4440',
                         '4464','4488','4512','4536','4560','4584',
                         '4608','4632','4656','4680','4704','4728',
                         '4752','4776','4800','4824','4848','4872',
                         '4896','4920','4944','4968','4992','5016',
                         '5040','5064','5088','5112','5136','5160'
                    ],
                },
                filename)
        except Exception as e:
            print(e)
            # Delete the partially downloaded file.
            if os.path.isfile(filename):
                os.remove(filename)
    return

# define the variables and the respective months to download as well as the
# desired region
variables = ['2m_temperature', 'snowfall', 'total_cloud_cover']
months = ['12', '11', '09']
lats = np.array([43.25, 46.00])
lons = np.array([-77.25, -73.25])
updatey = False

# depending on the month, download SEAS5.1 or try to download ERA5 instead
if month in ["07", "08", "09"]:
    for variable in variables:
        download_seas51(variable, month, year, out_dir + "SEAS51/", lats, lons)
elif month in ["10", "11"]:
    for variable in variables[0:2]:
        download_seas51(variable, month, year, out_dir + "SEAS51/", lats, lons)
    try:
        download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
    except:
        download_seas51(variables[2], month, year, out_dir + "SEAS51/", lats, lons)
        print("ERA5 " + variables[2] + " not downloaded, need to use SEAS5.1")
elif month == "12":
    for variable in variables[0:1]:
        download_seas51(variable, month, year, out_dir + "SEAS51/", lats, lons)
    try:
        download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
    except:
        download_seas51(variables[2], month, year, out_dir + "SEAS51/", lats, lons)
        print("ERA5 " + variables[2] + " not downloaded, need to use SEAS5.1")
    try:
        download_era5(variables[1], months[1], year, out_dir + "ERA5/", lats, lons)
    except:
        download_seas51(variables[1], month, year, out_dir + "SEAS51/", lats, lons)
        print("ERA5 " + variables[1] + " not downloaded, need to use SEAS5.1")
elif month in ["01", "02", "03", "04"]:
    year = str(int(year) - 1)
    try:
        download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
        updatey = True
    except:
        download_seas51(variables[2], month, year, out_dir + "SEAS51/", lats, lons)
        updatey = False
        print("ERA5 " + variables[2] + " not yet available, using SEAS5.1")
    try:
        download_era5(variables[1], months[1], year, out_dir + "ERA5/", lats, lons)
        updatey = True
    except:
        download_seas51(variables[1], month, year, out_dir + "SEAS51/", lats, lons)
        updatey = False
        print("ERA5 " + variables[1] + " not yet available, using SEAS5.1")
    try:
        download_era5(variables[0], months[0], year, out_dir + "ERA5/", lats, lons)
        updatey = True
    except:
        download_seas51(variables[0], month, year, out_dir + "SEAS51/", lats, lons)
        updatey = False
        print("ERA5 " + variables[0] + " not yet available, using SEAS5.1")
else:
    # if in May or June, make sure to reset the variable `frozen` to `False`
    # in preparation for the next winter's forecast
    with open(path + "auto/frozen", "r") as f:
        frozen = f.read()
    f.close()
    if frozen == "True":
        frozen = True
    else:
        frozen = False
    if frozen:
        frozen = False
        with open(path + "auto/frozen", "w") as f:
            f.write(str(frozen))
        f.close()
    print("no forecast can be made before July")

# save info on whether data was updated
with open(path + "downloads/updatem", "w") as f:
    f.write(str("True"))
f.close()
if updatey:
    with open(path + "downloads/updatey", "w") as f:
        f.write(str("True"))
    f.close()
