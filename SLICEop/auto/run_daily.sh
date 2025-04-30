#!/bin/bash
echo "---------- run_daily.sh -----------"
echo " "
date

requiredhost=crunch
local_path=/aos/home/jrieck/src/SLICEop/SLICEop
backup=/aos/home/jrieck/SLICEop_backup_data/

source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh

conda activate sliceop

echo False > ${local_path}/downloads/Twater/updated

printf "\nTrying to update Twater:\n"

if [[ `uname -a` == *${requiredhost}* ]]; then
    python ${local_path}/downloads/daily_Twater.py
    cp ${local_path}/downloads/Twater/Twater_Longueuil_updated.nc ${backup}
    updated=$(cat ${local_path}/downloads/Twater/updated)
else
    printf "\nHost is not $requiredhost, cannot access daily water temperature!\n"
fi

if [[ ${updated} == True ]]; then
    printf "\nPlotting water temperature.\n"
    python ${local_path}/auto/daily_plots.py
fi

printf "\nDownloading latest MODIS image:\n"
python ${local_path}/downloads/daily_MODIS.py

echo " "
echo "-----------------------------------"
