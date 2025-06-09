#!/bin/bash
local_path=$(echo $sliceop_path)

source $(echo $sliceop_conda_path)
conda activate sliceop

if [ ! -e ${local_path}/downloads/updatew ]; then
    echo False > ${local_path}/downloads/updatew
fi
if [ ! -e ${local_path}/downloads/updatem ]; then
    echo False > ${local_path}/downloads/updatem
fi
if [ ! -e ${local_path}/downloads/updatey ]; then
    echo False > ${local_path}/downloads/updatey
fi

if [ ! -e ${local_path}/prepro/preprow ]; then
    echo False > ${local_path}/prepro/preprow
fi
if [ ! -e ${local_path}/prepro/prepro ]; then
    echo False > ${local_path}/prepro/prepro
fi
if [ ! -e ${local_path}/prepro/preproy ]; then
    echo False > ${local_path}/prepro/preproy
fi

if [ ! -e ${local_path}/auto/forecastw ]; then
    echo False > ${local_path}/auto/forecastw
fi
if [ ! -e ${local_path}/auto/forecastm ]; then
    echo False > ${local_path}/auto/forecastm
fi
if [ ! -e ${local_path}/auto/frozen ]; then
    echo False > ${local_path}/auto/frozen
fi
if [ ! -e ${local_path}/auto/frozenDate ]; then
    echo 0 > ${local_path}/auto/frozenDate
fi

python ${local_path}/downloads/initial_download_ERA5.py
python ${local_path}/downloads/initial_Twater.py
