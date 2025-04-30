#!/bin/bash
echo "---------- run_yearly.sh -----------"
echo " "
date

local_path=/aos/home/jrieck/src/SLICEop/SLICEop

source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh

conda activate sliceop

echo False > ${local_path}/prepro/preproy
updatey=$(cat ${local_path}/downloads/updatey)
printf "\nPreprocessing:\n"
if [[ $updatey == True ]]; then
    python ${local_path}/prepro/yearly_preprocess.py
else
    printf "No preprocessing performed because SEAS5.1 and/or ERA5 could not be updated.\n"
fi

echo " "
echo "-----------------------------------"
