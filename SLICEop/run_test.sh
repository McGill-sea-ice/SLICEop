#!/bin/bash
local_path=$(echo $sliceop_path)

export TEST=True
d=1992-06-01
while [ "$d" != 2025-03-31 ]; do
    year=$(date -d "$d" +%Y)
    month=$(date -d "$d" +%m)
    dom=$(date -d "$d" +%d)
    weekday=$(date -d "$d" +%u)
    export YEAR="$year"; export MONTH="$month"; export DAY="$dom"
    if [[ "$month" == "06" && "$dom" == "10" ]]; then
        echo $d
        echo "False" > ${local_path}auto/frozen
    fi
    if [[ "$dom" == "07" ]]; then
        echo $d
        ${local_path}auto/run_monthly.sh
    fi
    if [[ "$weekday" == "1" ]]; then
        echo $d
        ${local_path}auto/run_weekly.sh
    fi
    d=$(date -I -d "$d + 1 day")
done
export TEST=False
