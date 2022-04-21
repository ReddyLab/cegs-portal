#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts.data_loading import load_bounds_2021_scceres_data; load_bounds_2021_scceres_data.run(\"$INPUT_FILE\")"
