''' initial_download_ERA5

This script downloads the required ERA5 data to define the three predictors
that will go into the Multiple Linear Regression (September total_cloud_cover,
November snowfall, December 2m_temperature). The range of years to download is
set by `start_year` and `end_year`.

'''
import os
import datetime
import cdsapi
import numpy as np

now = datetime.datetime.now()
path = os.environ["sliceop_path"]
out_dir = path + "downloads/ERA5/"

# set first and last year of range to download
start_year = 1992
end_year = 2023

# define a function that downloads the required ERA5 data
def download_era5(var, month, year, output_dir, lats, lons):
    # define filename and check if it is already present locally, if yes no
    # download is triggered.
    filename = output_dir + "ERA5_" + str(year) + month + "_" + var + ".grib"
    if os.path.isfile(filename):
        print(filename + " is already present, no need to download")
        return
    else:
        print("Downloading " + var + " for " + str(year) + month + " from ERA5")
        # using the Climate Data Store API to download the data
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
            # Delete the partially downloaded file in case something went wrong
            if os.path.isfile(filename):
                os.remove(filename)
    return

# define the variables and their respective months to download, as well as
# the region
variables = ['2m_temperature', 'snowfall', 'total_cloud_cover']
months = ['12', '11', '09']
lats = np.array([43.25, 46.00])
lons = np.array([-77.25, -73.25])

for year in range(start_year, end_year + 1):
    for variable, month in zip(variables, months):
        download_era5(variable, month, str(year), out_dir, lats, lons)
