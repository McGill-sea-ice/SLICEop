''' backup_yearly_ERA5

Download the monthly predictors from the reanalysis ERA5 in case it was not
downloaded previously during the monthly tasks. This script is a backup and is
only called if something went wrong in the normal procedure and the
required data has not yet been downloaded.

'''
import os
import datetime
import cdsapi
import numpy as np

# define paths
now = datetime.datetime.now()
path = os.environ["SLICEOP_PATH"]
out_dir = path + "/downloads/"

# if running TEST, take year, month, day from environment variables
# otherwise extract year, month, day from `datetime.datetime.now
if os.environ["TEST"]=="True":
    year = os.environ["YEAR"]
    month = os.environ["MONTH"]
    day = f"{(int(os.environ["DAY"]) -1):02d}"
else:
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

# define the variables and the respective months to download as well as the
# desired region
variables = ['2m_temperature', 'snowfall', 'total_cloud_cover']
months = ['12', '11', '09']
lats = np.array([43.25, 46.00])
lons = np.array([-77.25, -73.25])
updatey = False

# the ERA5 data from last year should have been downloaded in January the
# latest. If not, we try again from February to June. If by end of June it
# is still not downloaded, there are major issues with either the code
# or the ECMWF server and manual debugging has to be started

if month in ["02", "03", "04", "05", "06"]:
    year = str(int(year) - 1)
    try:
        download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
        updatey = True
    except:
        updatey = False
        print("Failed to download ERA5 " + variables[2] + ", trying again tomorrow.")
    try:
        download_era5(variables[1], months[1], year, out_dir + "ERA5/", lats, lons)
        updatey = True
    except:
        updatey = False
        print("Failed to download ERA5 " + variables[1] + ", trying again tomorrow.")
    try:
        download_era5(variables[0], months[0], year, out_dir + "ERA5/", lats, lons)
        updatey = True
    except:
        updatey = False
        print("Failed to download ERA5 " + variables[0] + ", trying again tomorrow.")
else:
    print("Failed to download ERA5 data after many months of trying, something is "
          + "very wrong. Check code and Climate Data Store.")

# save info on whether data was updated
if updatey:
    with open(path + "/downloads/updatey", "w") as f:
        f.write(str("True"))
    f.close()
