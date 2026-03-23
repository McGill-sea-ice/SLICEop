#!/bin/bash
# to be run each day, executing the updating and plotting the daily time series
# of water temperature in Longueuil downloading MODIS image
echo "---------- run_daily.sh -----------"
echo " "
date

# check if the required environment variables are set, if not run setup.sh
if [[ -z "${SLICEOP_PATH}" ]]; then
  if [ $# -eq 0 ]; then
    echo "run_daily.sh requires SLICEOP root directory as input argument"
    exit 1
  else
    source $1/setup.sh
    local_path=$(echo $SLICEOP_PATH)
  fi
else
  local_path=$(echo $SLICEOP_PATH)
fi

website=$(cat ${local_path}/echart/website)
if [[ ${website} == True ]]; then
    web_path=/storage2/tremblay-website/public_html
fi

# set 'requiredhost' because the daily water temperature data is only available
# on 'crunch'
requiredhost=$(echo $SLICEOP_TWATER_HOST)
# define path for backup data
backup=$(echo $SLICEOP_BACKUP_PATH)

# load conda environment
source $(echo $SLICEOP_CONDA_PATH)
conda activate sliceop

# check if updatey is 'True' , if not, something went wrong and we need to
# download ERA5 data for the previous year.
updatey=$(cat ${local_path}/downloads/updatey)
if [[ ${updatey} == False ]]; then
    printf "\nUpdating last year's ERA5 data:\n"
    python ${local_path}/downloads/backup_yearly_ERA5.py
fi

# check if updatem is 'True' , if not, something went wrong and we need to
# run run_monthly.sh again.
updatem=$(cat ${local_path}/downloads/updatem)
if [[ ${updatem} == False ]]; then
    ${local_path}/auto/run_monthly.sh
fi

# check if updatem is 'True' , if not, something went wrong and we need to
# run run_monthly.sh again.
updatew=$(cat ${local_path}/downloads/updatew)
if [[ ${updatew} == False ]]; then
    ${local_path}/auto/run_weekly.sh
fi

# make sure 'updated' is False, indicating that the daily update was not
# yet succesful (will be set to True within daily_Twater.py if successful)
echo False > ${local_path}/downloads/Twater/updated

printf "\nTrying to update Twater:\n"
# only run update if script is executed from host 'requiredhost'
if [[ `uname -a` == *${requiredhost}* ]]; then
    # update the time series of water temperature
    python ${local_path}/downloads/daily_Twater.py
    # copy the time series to a backup location
    cp ${local_path}/downloads/Twater/Twater_Longueuil_updated.nc ${backup}
    # check if update was successful (updated=True)
    updated=$(cat ${local_path}/downloads/Twater/updated)
else
    printf "\nHost is not $requiredhost, cannot access daily water"\
        " temperature.\n"
fi
# download the latest MODIS stellite image of the Montreal region from NASA
# worldview
printf "\nDownloading latest MODIS image:\n"
python ${local_path}/downloads/daily_MODIS.py

# download the latest Sentinel2 stellite image of the Montreal region from
# Copernicus
printf "\nDownloading latest Sentinel2 image:\n"
python ${local_path}/downloads/daily_sentinel.py

# plots
printf "\nPlotting daily plots.\n"
python ${local_path}/auto/daily_plots.py

# update data that is used in echart
printf "\nPreparing data to be plotted in echart:\n"
python ${local_path}/auto/daily_prepare_data_for_echart.py
if [[ ${website} == True ]]; then
    cp ${local_path}/echart/frozen.json ${web_path}/data/sliceop_frozen.json
    cp ${local_path}/echart/latest.json ${web_path}/data/sliceop_latest.json
    cp ${local_path}/echart/colormap.json ${web_path}/data/sliceop_colormap.json
    cp ${local_path}/echart/fuds.json ${web_path}/data/sliceop_fuds.json
    cp ${local_path}/echart/sliceop_data.json ${web_path}/data/sliceop_data.json
    cp ${local_path}/echart/worldview.dot.png ${web_path}/images/worldview.dot.png
    cp ${local_path}/echart/sentinel2.dot.png ${web_path}/images/sentinel2.dot.png
fi

# make a backup of the raw thermistor data
printf "\nCreating backup of raw thermistor data\n"
if [[ `uname -a` == *${requiredhost}* ]]; then
    rsync -auv /storage/thermistor/*.dat ${local_path}/downloads/Twater/raw/
fi

echo " "
echo "-----------------------------------"
