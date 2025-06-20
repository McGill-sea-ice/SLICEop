''' weekly_ERA5

Download an update of the monthly predictors from the reanalysis ERA5 to replace
the SEAS5.1 data of the current month if possible.
Example: On September 7, we download the new SEAS5.1 seasonal forecasts Sept. cloud cover, Nov. snowfall, Dec. 2m temperature and run the forecast. On September 23, ERA5 reanalysis cloud cover is already partially available for
September, so we can download that and replace the SEAS5.1 September cloud cover
for Sept. 1 - ~Sept. 18 with ERA5 data before computing the monthly average.
(Note that this script only downloads the data, the rest is done during
preprocessing.)

'''
import os
import datetime
import cdsapi
import numpy as np

# define paths
now = datetime.datetime.now()
path = os.environ["sliceop_path"]
out_dir = path + "/downloads/"

# if running TEST, take year, month, day from environment variables
# otherwise extract year, month, day from `datetime.datetime.now
if os.environ["TEST"]=="True":
    year = os.environ["YEAR"]
    month = os.environ["MONTH"]
    day = int(os.environ["DAY"])
else:
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"
    day = int(now.day)

# define a function to download the ERA5 data
def download_era5(var, month, year, output_dir, lats, lons):
    # define the filename. if a file of this name is already present locally,
    # it will be replaced by the more recent version
    filename = output_dir + "ERA5_" + str(year) + month + "_" + var + ".partial.grib"
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
                # API ignores cases where there are less than 31 days, for
                # example if we run this script on the 20th of the month, ERA5
                # data might be available only up to the 16th and thus days
                # `01` to `16` will be downloaded, the other days ignored
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

def download_era5_test(var, month, year, max_day, output_dir, lats, lons):
    filename = output_dir + "ERA5_" + str(year) + month + "_" + var + ".partial.grib"
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
                'day': [f"{np.arange(1, max_day+1)[i]:02d}" for i in range(0, max_day)],
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


# define the variables and the respective months to download as well as the
# desired region
variables = ['2m_temperature', 'snowfall', 'total_cloud_cover']
months = ['12', '11', '09']
lats = np.array([43.25, 46.00])
lons = np.array([-77.25, -73.25])

if os.environ["TEST"]=="True":
    if month == "09":
        if max_day > 0:
            try:
                download_era5(variables[2], months[2], year, max_day, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[2] + " not downloaded")
    elif month == "10":
        if day < 7:
            if max_day > 0:
                max_day = 30
            else:
                max_day = 30 + max_day
            try:
                download_era5(variables[2], months[2], year, max_day, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[2] + " not downloaded")
        else:
            try:
                os.remove(local_path + "downloads/ERA5/ERA5_"
                          + year + months[2] + "_" + variables[2] +  ".partial.grib")
            except:
                pass
    elif month == "11":
        if max_day > 0:
            try:
                download_era5(variables[1], months[1], year, max_day, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[1] + " not downloaded")
    elif month == "12":
        if day < 7:
            if max_day > 0:
                max_day1 = 30
                try:
                    download_era5(variables[1], months[1], year, max_day1, out_dir + "ERA5/", lats, lons)
                    download_era5(variables[0], months[0], year, max_day, out_dir + "ERA5/", lats, lons)
                except:
                    print("ERA5 " + variables[1] + " and " + variables[0] + " not downloaded")
            else:
                max_day1 = 30 + max_day
                try:
                    download_era5(variables[1], months[1], year, max_day1, out_dir + "ERA5/", lats, lons)
                except:
                    print("ERA5 " + variables[1] + " and " + variables[0] + " not downloaded")
        else:
            try:
                os.remove(local_path + "downloads/ERA5/ERA5_"
                          + year + months[1] + "_" + variables[1] +  ".partial.grib")
            except:
                pass
            try:
                download_era5(variables[0], months[0], year, max_day, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[0] + " not downloaded")
    elif month == "01":
        year = str(int(year) - 1)
        if day < 7:
            if max_day > 0:
                max_day = 31
            else:
                max_day = 31 + max_day
            try:
                download_era5(variables[0], months[0], year, max_day, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[0] + " not downloaded")
        else:
            try:
                os.remove(local_path + "downloads/ERA5/ERA5_"
                          + year + months[0] + "_" + variables[0] +  ".partial.grib")
            except:
                pass
    else:
        with open(local_path + "/auto/frozen", "r") as f:
            frozen = f.read()
        f.close()
        if frozen == "True":
            frozen = True
        else:
            frozen = False
        if frozen:
            frozen = False
            with open(local_path + "/auto/frozen", "w") as f:
                f.write(str(frozen))
            f.close()
        print("No additional data found to improve the forecast ")
else:
    # depending on the month try to download ERA5 if it should be available
    if month == "09":
        # do not replace SEAS5.1 cloud cover with ERA5 before the new SEAS5.1
        # forecast is downloaded on the 7th
        if day > 6:
            try:
                download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[2] + " not downloaded")
    elif month == "10":
        # only try to update SEAS5.1 cloud cover with ERA5 before the whole month
        # of Sept. cloud cover is downloaded from ERA5 on the 7th
        if day < 7:
            try:
                download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
            except:
       	        print("ERA5 " + variables[2] + " not downloaded")
        else:
            try:
                os.remove(path + "/downloads/ERA5/ERA5_"
                          + year + months[2] + "_" + variables[2] +  ".partial.grib")
            except:
                pass
    elif month == "11":
        # do not replace SEAS5.1 snowfall with ERA5 before the new SEAS5.1
        # forecast is downloaded on the 7th
        if day > 6:
            try:
                download_era5(variables[1], months[1], year, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[1] + " not downloaded")
    elif month == "12":
        # only try to update SEAS5.1 2m temperature with ERA5 before the whole
        # month of Dec. 2m temperature is downloaded from ERA5 on the 7th and
        # do not replace SEAS5.1 2m temperature with ERA5 before the new SEAS5.1
        # forecast is downloaded on the 7th
        if day < 7:
            try:
                download_era5(variables[1], months[1], year, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[1] + " not downloaded")
        else:
            try:
                os.remove(path + "/downloads/ERA5/ERA5_"
                        + year + months[1] + "_" + variables[1] +  ".partial.grib")
            except:
                pass
            try:
                download_era5(variables[0], months[0], year, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[0] + " not downloaded")
    elif month == "01":
        # even in `year+1` we need the predictors from `year`
        year = str(int(year) - 1)
        # only try to update SEAS5.1 2m temperature with ERA5 before the whole
        # month of Dec. 2m temperature is downloaded from ERA5 on the 7th
        if day < 7:
            try:
                download_era5(variables[0], months[0], year, out_dir + "ERA5/", lats, lons)
            except:
                print("ERA5 " + variables[0] + " not downloaded")
        else:
            try:
                os.remove(path + "/downloads/ERA5/ERA5_"
                        + year + months[0] + "_" + variables[0] +  ".partial.grib")
            except:
                pass
    else:
        # if in May or June, make sure to reset the variable `frozen` to `False`
        # in preparation for the next winter's forecast
        with open(path + "/auto/frozen", "r") as f:
            frozen = f.read()
        f.close()
        if frozen == "True":
            frozen = True
        else:
            frozen = False
        if frozen:
            frozen = False
        with open(path + "/auto/frozen", "w") as f:
            f.write(str(frozen))
        f.close()
        print("No additional data found to improve the forecast ")

# save info on whether data was updated
with open(path + "/downloads/updatew", "w") as f:
    f.write(str("True"))
f.close()
