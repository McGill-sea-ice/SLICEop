#!/bin/bash
echo "---------- run_weekly.sh -----------"
echo " "
#date
echo ${YEAR}"-"${MONTH}"-"${DAY}

source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh

conda activate sliceop

echo "False" > /storage/jrieck/SLICEop/test/downloads/updatew
echo "False" > /storage/jrieck/SLICEop/test/prepro/preprow
echo "False" > /storage/jrieck/SLICEop/test/auto/forecastw

printf "\nUpdating ERA5:\n"

python /storage/jrieck/SLICEop/test/downloads/weekly_ERA5.py
updatew=$(cat /storage/jrieck/SLICEop/test/downloads/updatew)

printf "\nPreprocessing:\n"

if [[ "$updatew" == "True" ]]; then
    python /storage/jrieck/SLICEop/test/prepro/weekly_preprocess.py
else
    printf "No preprocessing performed because ERA5 could not be updated.\n"
fi

frozen=$(cat /storage/jrieck/SLICEop/test/auto/frozen)
preprow=$(cat /storage/jrieck/SLICEop/test/prepro/preprow)

if [[ "$frozen" == "False" ]]; then
    if [[ "$preprow" == "True" ]]; then
        printf "\nForecast running\n"
        python /storage/jrieck/SLICEop/test/auto/weekly_forecast.py
        forecastw=$(cat /storage/jrieck/SLICEop/test/auto/forecastw)
    else
        printf "\nNo forecast issued because the preprocessing was not successful"
    fi
else
    printf "\nNo forecast issued because St. Lawrence is already frozen"
fi

python /storage/jrieck/SLICEop/test/auto/weekly_plots.py

echo " "
echo "-----------------------------------"
