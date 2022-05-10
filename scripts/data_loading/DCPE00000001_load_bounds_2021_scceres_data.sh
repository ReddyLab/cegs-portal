#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts.data_loading import DCPE00000001_load_bounds_2021_scceres_data; DCPE00000001_load_bounds_2021_scceres_data.run(\"$INPUT_FILE\")"
