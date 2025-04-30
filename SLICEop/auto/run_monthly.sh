#!/bin/bash
echo "---------- run_monthly.sh -----------"
echo " "
date

local_path=/aos/home/jrieck/src/SLICEop/SLICEop

source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh

conda activate sliceop

echo False > ${local_path}/auto/forecastm
preproy=$(cat ${local_path}/prepro/preproy)
if [[ ${preproy} == False ]]; then
    printf "Yearly update of monthly predictors failed, cannot continue!"
else
    echo False > ${local_path}/downloads/updatem
    echo False > ${local_path}/prepro/prepro
    printf "\nUpdating SEAS5.1 and/or ERA5:\n"
    python ${local_path}/monthly_SEAS51_ERA5.py
    updatem=$(cat ${local_path}/downloads/updatem)
    printf "\nPreprocessing:\n"
    if [[ ${updatem} == True ]]; then
        python ${local_path}/prepro/monthly_preprocess.py
    else
        printf "No preprocessing performed because SEAS5.1 and/or ERA5 could not be updated.\n"
    fi
    frozen=$(cat ${local_path}/auto/frozen)
    prepro=$(cat ${local_path}/prepro/prepro)
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

forecastm=$(cat ${local_path}/auto/forecastm)
if [[ ${forecastm} == True ]]; then
    python ${local_path}/auto/monthly_plots.py
fi


echo " "
echo "-----------------------------------"
