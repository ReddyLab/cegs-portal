#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000001_load_bounds_2021_scceres_data; DCPEXPR00000001_load_bounds_2021_scceres_data.run(\"${INPUT_FILE}\")"
