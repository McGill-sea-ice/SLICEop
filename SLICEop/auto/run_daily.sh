#!/bin/bash
# to be run each day, executing the updating and plotting the daily time series
# of water temperature in Longueuil downloading MODIS image
echo "---------- run_daily.sh -----------"
echo " "
date

# set 'requiredhost' because the daily water temperature data is only available
# on 'crunch'
requiredhost=crunch
# define path to SLICEop
local_path=/aos/home/jrieck/src/SLICEop/SLICEop
backup=/aos/home/jrieck/SLICEop_backup_data/

# load conda environment
source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh
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

echo " "
echo "-----------------------------------"
