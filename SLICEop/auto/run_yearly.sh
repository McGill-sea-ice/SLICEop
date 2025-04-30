#!/bin/bash
echo "---------- run_yearly.sh -----------"
echo " "
#date
echo ${YEAR}"-"${MONTH}"-"${DAY}

source /aos/home/jrieck/miniconda3/etc/profile.d/conda.sh

conda activate sliceop

echo "False" > /storage/jrieck/SLICEop/test/prepro/preproy
updatey=$(cat /storage/jrieck/SLICEop/test/downloads/updatey)
printf "\nPreprocessing:\n"
if [[ "$updatey" == "True" ]]; then
    python /storage/jrieck/SLICEop/test/prepro/yearly_preprocess.py
else
    printf "No preprocessing performed because SEAS5.1 and/or ERA5 could not be updated.\n"
fi

echo " "
echo "-----------------------------------"
