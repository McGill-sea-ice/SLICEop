#!/bin/bash
if [[ -z "${SLICEOP_PATH}" ]]; then
  local_path=$(echo $SLICEOP_PATH)
else
  echo "execute SLICEOP/setup.sh before running echart_cheat.sh"
  exit 1
fi

# to avoid needing to set up a html server etc. to get the data loaded into
# the echart, we just convert the data from json into javascript-compliant
# files so we load it into the echart as scripts not as data
{ echo -n 'datain='; cat ${path}/echart/sliceop_data.json; } > ${path}/echart/sliceop_data.js

{ echo -n 'color='; cat ${path}/echart/colormap.json; } > ${path}/echart/colormap.js

{ echo -n 'fud='; cat ${path}/echart/fuds.json; } > ${path}/echart/fuds.js
