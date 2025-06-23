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
else
  local_path=$(echo $SLICEOP_PATH)
fi

# set 'requiredhost' because the daily water temperature data is only available
# on 'crunch'
requiredhost=$(echo $SLICEOP_TWATER_HOST)
# define path for backup data
backup=$(echo $SLICEOP_BACKUP_PATH)

# load conda environment
source $(echo $SLICEOP_CONDA_PATH)
conda activate sliceop

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
        " temperature!\n"
fi
# plot time series if update was successful
if [[ ${updated} == True ]]; then
    printf "\nPlotting water temperature.\n"
    python ${local_path}/auto/daily_plots.py
fi

# download the latest MODIS stellite image of the Montreal region from NASA
# worldview
printf "\nDownloading latest MODIS image:\n"
python ${local_path}/downloads/daily_MODIS.py

# update data that is used in echart
printf "\nPreparing data to be plotted in echart:\n"
python ${local_path}/auto/daily_prepare_data_for_echart.py

echo " "
echo "-----------------------------------"
