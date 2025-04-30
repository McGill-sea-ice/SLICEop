#!/bin/bash
echo "---------- run_weekly.sh -----------"
echo " "
date

local_path=/aos/home/jrieck/src/SLICEop/SLICEop

source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh

conda activate sliceop

echo "False" > ${local_path}/downloads/updatew
echo "False" > ${local_path}/prepro/preprow
echo "False" > ${local_path}/auto/forecastw

printf "\nUpdating ERA5:\n"

python ${local_path}/downloads/weekly_ERA5.py
updatew=$(cat ${local_path}/downloads/updatew)

printf "\nPreprocessing:\n"

if [[ $updatew == True ]]; then
    python ${local_path}/prepro/weekly_preprocess.py
else
    printf "No preprocessing performed because ERA5 could not be updated.\n"
fi

frozen=$(cat ${local_path}/auto/frozen)
preprow=$(cat ${local_path}/prepro/preprow)

if [[ ${frozen} == False ]]; then
    if [[ ${preprow} == True ]]; then
        printf "\nForecast running\n"
        python ${local_path}/auto/weekly_forecast.py
        forecastw=$(cat ${local_path}/auto/forecastw)
    else
        printf "\nNo forecast issued because the preprocessing was not successful"
    fi
else
    printf "\nNo forecast issued because St. Lawrence is already frozen"
fi

python ${local_path}/auto/weekly_plots.py

echo " "
echo "-----------------------------------"
