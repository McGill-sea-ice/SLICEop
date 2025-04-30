import os
import datetime
import cdsapi
import numpy as np

now = datetime.datetime.now()
out_dir = "/storage/jrieck/SLICEop/downloads/ERA5/"

# initially download era5 data up to last year and save it to netcdf

def download_era5(var, month, year, output_dir, lats, lons):
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

start_year = 2002
end_year = 2023

variables = ['2m_temperature', 'snowfall', 'total_cloud_cover']
months = ['12', '11', '09']
lats = np.array([43.25, 46.00])
lons = np.array([-77.25, -73.25])

for year in range(start_year, end_year + 1):
    for variable, month in zip(variables, months):
        download_era5(variable, month, str(year), out_dir, lats, lons)
