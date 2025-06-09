#!/bin/bash
# to be run on the 7th of each month, executing the monthly downloads,
# preprocessing, and forecast
echo "---------- run_monthly.sh -----------"
echo " "
date

# define path to SLICEop
local_path=$(echo $sliceop_path)

# load conda environment
source $(echo $sliceop_conda_path)
conda activate sliceop

# make sure 'forecastm' is False, indicating that the monthly forecast was not
# yet succesful (will be set to True within monthly_forecast.py if successful)
echo False > ${local_path}/auto/forecastm
# load boolean 'preproy' indicating whether the yearly preprocessing was
# succesful, can only continue if it was
preproy=$(cat ${local_path}/prepro/preproy)
if [[ ${preproy} == False ]]; then
    printf "Yearly update of monthly predictors failed, cannot continue!"
else
    # make sure 'updatem' and 'prepro' are False, indicating that the monthly
    # download and preprocessing were not yet succesful (will be set to True
    # within monthly_SEAS51_ERA5.py and monthly_preprocess.py if successful)
    echo False > ${local_path}/downloads/updatem
    echo False > ${local_path}/prepro/prepro
    printf "\nUpdating SEAS5.1 and/or ERA5:\n"
    # downloading data from ECMWF
    python ${local_path}/downloads/monthly_SEAS51_ERA5.py
    # check if download was successful (updatem=True)
    updatem=$(cat ${local_path}/downloads/updatem)
    printf "\nPreprocessing:\n"
    # do preprocessing if downloads were successful
    if [[ ${updatem} == True ]]; then
        python ${local_path}/prepro/monthly_preprocess.py
    else
        printf "No preprocessing performed because SEAS5.1 and/or ERA5 could not be updated.\n"
    fi
    # load booleans 'frozen' (True if river is already frozen) and 'prepro'
    # (True if monthly preprocessing was successful)
    frozen=$(cat ${local_path}/auto/frozen)
    prepro=$(cat ${local_path}/prepro/prepro)
    # only perform forecast if the river is not frozen and the monthly
    # preprocessing was successful
    if [[ ${frozen} == False ]]; then
        if [[ ${prepro} == True ]]; then
            printf "\nForecast running\n"
            python ${local_path}/auto/monthly_forecast.py
        else
            printf "\nNo forecast issued because the preprocessing was not successful"
        fi
    else
        printf "\nNo forecast issued because St. Lawrence is already frozen"
    fi
fi

# if monthly forecast was successful, plot the data
forecastm=$(cat ${local_path}/auto/forecastm)
if [[ ${forecastm} == True ]]; then
    python ${local_path}/auto/monthly_plots.py
fi


echo " "
echo "-----------------------------------"
