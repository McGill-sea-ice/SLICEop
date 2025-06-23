#!/bin/bash
# to be run once a year, executing the yearly preprocessing
echo "---------- run_yearly.sh -----------"
echo " "
date

# check if the required environment variables are set, if not run setup.sh
if [[ -z "${SLICEOP_PATH}" ]]; then
  if [ $# -eq 0 ]; then
    echo "run_yearly.sh requires SLICEOP root directory as input argument"
    exit 1
  else
    source $1/setup.sh
    local_path=$(echo $SLICEOP_PATH)
  fi
else
  local_path=$(echo $SLICEOP_PATH)
fi

# load conda environment
source $(echo $SLICEOP_CONDA_PATH)
conda activate sliceop

# make sure 'preproy' is False, indicating that the yearly preprocessing was not
# succesful (will be set to True within yearly_preprocess.py if succesful)
echo False > ${local_path}/prepro/preproy
# load boolean 'updatey' which should be True if the necessary downloads to run
# the yearly preprocessing were succesful
updatey=$(cat ${local_path}/downloads/updatey)
printf "\nPreprocessing:\n"
# run preprocessing if 'updatey' is True
if [[ $updatey == True ]]; then
    python ${local_path}/prepro/yearly_preprocess.py
else
    printf "No preprocessing performed because SEAS5.1 and/or ERA5 could not"\
           " be updated.\n"
fi

echo " "
echo "-----------------------------------"
