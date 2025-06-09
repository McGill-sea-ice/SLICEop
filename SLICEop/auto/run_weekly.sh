#!/bin/bash
# to be run every Monday, executing the weekly downloads,
# preprocessing, and forecast
echo "---------- run_weekly.sh -----------"
echo " "
date

# define path to SLICEop
local_path=$(echo $sliceop_path)

# load conda environment
source $(echo $sliceop_conda_path)
conda activate sliceop

# make sure 'updatew', 'preprow', and 'forecastw' are all False, indicating
# that the weekly downloads, preprocessing, and forecast were not yet
# successful (will be set to True within weekly_ERA5.py, weekly_preprocess.py
# and weekly_forecast.py if successful)
echo "False" > ${local_path}/downloads/updatew
echo "False" > ${local_path}/prepro/preprow
echo "False" > ${local_path}/auto/forecastw

# load boolean 'preproy' indicating whether the yearly preprocessing was
# succesful, can only continue if it was
preproy=$(cat ${local_path}/prepro/preproy)
if [[ ${preproy} == False ]]; then
    printf "Yearly update of monthly predictors failed, cannot continue!"
else
    printf "\nUpdating ERA5:\n"
    # downloading data from ECMWF
    python ${local_path}/downloads/weekly_ERA5.py
    # check if download was successful (updatew=True)
    updatew=$(cat ${local_path}/downloads/updatew)
    printf "\nPreprocessing:\n"
    # do preprocessing if downloads were successful
    if [[ $updatew == True ]]; then
        python ${local_path}/prepro/weekly_preprocess.py
    else
        printf "No preprocessing performed because ERA5 could not be updated.\n"
    fi
    # load booleans 'frozen' (True if river is already frozen) and 'preprow'
    # (True if weekly preprocessing was successful)
    frozen=$(cat ${local_path}/auto/frozen)
    preprow=$(cat ${local_path}/prepro/preprow)
    # only perform forecast if the river is not frozen and the weekly
    # preprocessing was successful
    if [[ ${frozen} == False ]]; then
        if [[ ${preprow} == True ]]; then
            printf "\nForecast running\n"
            python ${local_path}/auto/weekly_forecast.py
        else
            printf "\nNo forecast issued because the preprocessing was not successful"
        fi
    else
        printf "\nNo forecast issued because St. Lawrence is already frozen"
    fi
fi

# if weekly forecast was successful, plot the data
forecastw=$(cat ${local_path}/auto/forecastw)
if [[ ${forecastm} == True ]]; then
    python ${local_path}/auto/weekly_plots.py
fi

echo " "
echo "-----------------------------------"
