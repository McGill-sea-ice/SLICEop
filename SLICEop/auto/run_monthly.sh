#!/bin/bash
echo "---------- run_monthly.sh -----------"
echo " "
#date
echo ${YEAR}"-"${MONTH}"-"${DAY}

source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh

conda activate sliceop

echo "False" > /storage/jrieck/SLICEop/test/auto/forecastm
preproy=$(cat /storage/jrieck/SLICEop/test/prepro/preproy)
if [[ "$preproy" == "False" ]]; then
    printf "Yearly update of monthly predictors failed, cannot continue!"
else
    echo "False" > /storage/jrieck/SLICEop/test/downloads/updatem
    echo "False" > /storage/jrieck/SLICEop/test/prepro/prepro
    printf "\nUpdating SEAS5.1 and/or ERA5:\n"
    python /storage/jrieck/SLICEop/test/downloads/monthly_SEAS51_ERA5.py
    updatem=$(cat /storage/jrieck/SLICEop/test/downloads/updatem)
    printf "\nPreprocessing:\n"
    if [[ "$updatem" == "True" ]]; then
        python /storage/jrieck/SLICEop/test/prepro/monthly_preprocess.py
    else
        printf "No preprocessing performed because SEAS5.1 and/or ERA5 could not be updated.\n"
    fi
    frozen=$(cat /storage/jrieck/SLICEop/test/auto/frozen)
    prepro=$(cat /storage/jrieck/SLICEop/test/prepro/prepro)
    if [[ "$frozen" == "False" ]]; then
        if [[ "$prepro" == "True" ]]; then
            printf "\nForecast running\n"
            python /storage/jrieck/SLICEop/test/auto/monthly_forecast.py
        else
            printf "\nNo forecast issued because the preprocessing was not successful"
        fi
    else
        printf "\nNo forecast issued because St. Lawrence is already frozen"
    fi
fi

forecastm=$(cat /storage/jrieck/SLICEop/test/auto/forecastm)
if [[ "$forecastm" == "True" ]]; then
    python /storage/jrieck/SLICEop/test/auto/monthly_plots.py
fi


echo " "
echo "-----------------------------------"
