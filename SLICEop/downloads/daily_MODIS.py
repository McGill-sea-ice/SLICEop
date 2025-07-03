'''daily_MODIS

Download the MODIS/Terra true color image from the day before from NASA
worldview within 45.1855N - 45.8297N, 74.2417W - 73.261W

'''
import os
import datetime
import requests

now = datetime.datetime.now()
# specify directory to store the downloaded image
path = os.environ["SLICEOP_PATH"]
out_dir = path + "/downloads/MODIS/"

# extract year, month and day from datetime.datetime.now()
year = f"{now.year:04d}"
month = f"{now.month:02d}"
day = f"{(now.day - 1):02d}"

print("Downloading MODIS satellite image for " + year + "-" + month + "-" + day)

# define url to download image
# to define different limits of the shown image, change
# BBOX=45.1855,-74.2417,45.8297,-73.261
url = str("https://wvs.earthdata.nasa.gov/api/v1/"
          + "snapshot?REQUEST=GetSnapshot&"
          + "TIME=" + year +"-" + month + "-" + day + "T00:00:00Z"
          + "&BBOX=45.1855,-74.2417,45.8297,-73.261&"
          + "CRS=EPSG:4326&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor,"
          + "Coastlines_15m&WRAP=day,x&FORMAT=image/jpeg"
          + "&WIDTH=893&HEIGHT=586&colormaps=,&ts=1744122633289")

# download image and save to out_dir
with open(out_dir + 'worldview.jpg', 'wb') as handle:
    response = requests.get(url, stream=True)
    if not response.ok:
        print(response)
    for block in response.iter_content(1024):
        if not block:
            break
        handle.write(block)
