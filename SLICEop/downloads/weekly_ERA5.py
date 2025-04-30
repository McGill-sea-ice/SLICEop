import os
import datetime
import cdsapi
import numpy as np

now = datetime.datetime.now()
local_path = "/aos/home/jrieck/src/SLICEop/SLICEop/"
out_dir = local_path + "downloads/"

year = f"{now.year:04d}"
month = f"{now.month:02d}"
day = int(now.day)

def download_era5(var, month, year, output_dir, lats, lons):
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

variables = ['2m_temperature', 'snowfall', 'total_cloud_cover']
months = ['12', '11', '09']
lats = np.array([43.25, 46.00])
lons = np.array([-77.25, -73.25])

if month == "09":
    if day > 6:
        try:
            download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
        except:
            print("ERA5 " + variables[2] + " not downloaded")
elif month == "10":
    if day < 7:
        try:
            download_era5(variables[2], months[2], year, out_dir + "ERA5/", lats, lons)
        except:
       	    print("ERA5 " + variables[2] + " not downloaded")
    else:
        try:
            os.remove(local_path + "downloads/ERA5/ERA5_"
                      + year + months[2] + "_" + variables[2] +  ".partial.grib")
        except:
            pass
elif month == "11":
    if day > 6:
        try:
            download_era5(variables[1], months[1], year, out_dir + "ERA5/", lats, lons)
        except:
            print("ERA5 " + variables[1] + " not downloaded")
elif month == "12":
    if day < 7:
        try:
            download_era5(variables[1], months[1], year, out_dir + "ERA5/", lats, lons)
        except:
            print("ERA5 " + variables[1] + " not downloaded")
    else:
        try:
            os.remove(local_path + "downloads/ERA5/ERA5_"
                      + year + months[1] + "_" + variables[1] +  ".partial.grib")
        except:
            pass
        try:
            download_era5(variables[0], months[0], year, out_dir + "ERA5/", lats, lons)
        except:
            print("ERA5 " + variables[0] + " not downloaded")
elif month == "01":
    year = str(int(year) - 1)
    if day < 7:
        try:
            download_era5(variables[0], months[0], year, out_dir + "ERA5/", lats, lons)
        except:
            print("ERA5 " + variables[0] + " not downloaded")
    else:
        try:
            os.remove(local_path + "downloads/ERA5/ERA5_"
                      + year + months[0] + "_" + variables[0] +  ".partial.grib")
        except:
            pass
else:
    with open(local_path + "auto/frozen", "r") as f:
        frozen = f.read()
    f.close()
    if frozen == "True":
        frozen = True
    else:
        frozen = False
    if frozen:
        frozen = False
        with open(local_path + "auto/frozen", "w") as f:
            f.write(str(frozen))
        f.close()
    print("No additional data found to improve the forecast ")

# save info on whether data was updated
with open(local_path + "downloads/updatew", "w") as f:
    f.write(str("True"))
f.close()
