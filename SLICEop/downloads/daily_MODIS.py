import os
import datetime
import requests

now = datetime.datetime.now()
out_dir = "/storage/jrieck/SLICEop/test/downloads/MODIS/"

#year = f"{now.year:04d}"
#month = f"{now.month:02d}"
#day = f"{(now.day - 1):02d}"

year = os.environ["YEAR"]
month = os.environ["MONTH"]
day = f"{int(os.environ["DAY"])-1:02d}"

print("Downloading MODIS satellite image for " + year + "-" + month + "-" + day)

url = str("https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&"
          + "TIME=" + year +"-" + month + "-" + day + "T00:00:00Z&BBOX=45.1855,-74.2417,45.8297,-73.261&"
          + "CRS=EPSG:4326&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor,Coastlines_15m&WRAP=day,"
          + "x&FORMAT=image/jpeg&WIDTH=893&HEIGHT=586&colormaps=,&ts=1744122633289")

with open(out_dir + 'worldview.jpg', 'wb') as handle:
    response = requests.get(url, stream=True)
    if not response.ok:
        print(response)
    for block in response.iter_content(1024):
        if not block:
            break
        handle.write(block)
