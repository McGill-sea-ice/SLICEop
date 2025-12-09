'''daily_sentinel

Download the SENTINEL2 true color image from within the days 
before from COPERNICUS (45.3N - 45.75N, 74.2W - 73.25W

'''
import os
import datetime
import getpass
import sentinelhub as sh
from matplotlib import pyplot as plt

config = sh.SHConfig("cdse")

now = datetime.datetime.now()
# specify directory to store the downloaded image
path = os.environ["SLICEOP_PATH"]
out_dir = path + "/downloads/sentinel/"

# extract year, month and day from datetime.datetime.now()
year = f"{now.year:04d}"
month = f"{now.month:02d}"
day = f"{(now.day - 1):02d}"

print("Downloading SENTINEL2 satellite image around " + year + "-" + month + "-" + day)

mtl_box = (-74.3, 45.3, -73.2, 45.75)
resolution = 40
mtl_bbox = sh.BBox(bbox=mtl_box, crs=sh.CRS.WGS84)
mtl_size = sh.bbox_to_dimensions(mtl_bbox, resolution=resolution)
t_start = str(now - datetime.timedelta(28))[0:10]
t_end = str(now)[0:10]

evalscript_true_color = """
    //VERSION=3

    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04"]
            }],
            output: {
                bands: 3
            }
        };
    }

    function updateOutputMetadata(scenes, inputMetadata, outputMetadata) {
          outputMetadata.userData = { scenes: scenes.tiles }
    }

    function evaluatePixel(sample) {
        return [sample.B04, sample.B03, sample.B02];
    }
"""

request_true_color = sh.SentinelHubRequest(
    evalscript=evalscript_true_color,
    input_data=[
        sh.SentinelHubRequest.input_data(
            data_collection=sh.DataCollection.SENTINEL2_L2A.define_from(
                "s2l2a", service_url=config.sh_base_url
            ),
            time_interval=(t_start, t_end),
            other_args={"dataFilter": {"maxCloudCoverage": 80}}
        )
    ],
    responses=[
        {
            "identifier": "default",
            "format": {"type": "image/png"},
        },
        {
            "identifier": "userdata",
            "format": {"type": "application/json"},
        },
    ],
    bbox=mtl_bbox,
    size=mtl_size,
    config=config,
)

response = request_true_color.get_data()
true_color_imgs = response[0]["default.png"]
metadata = response[0]["userdata.json"]

dpi = 80
height, width, nbands = true_color_imgs.shape
figsize = width / float(dpi), height / float(dpi)
fig = plt.figure(figsize=figsize)
ax = fig.add_axes([0, 0, 1, 1])
ax.axis('off')
ax.imshow(true_color_imgs/255*2, interpolation='nearest')
plt.savefig(out_dir + 'sentinel2.png', dpi=dpi)

date = [metadata["scenes"][i]["date"] for i in range(0, len(metadata["scenes"])) if "N0511_R054" in metadata["scenes"][i]["productId"]][0]
with open(out_dir + "sentinel_date", "w") as f:
    f.write(date[0:10])
f.close()
