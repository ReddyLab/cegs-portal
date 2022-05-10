#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts.data_loading import DCPE00000004_load_bounds_scCERES_mhc_2021; DCPE00000004_load_bounds_scCERES_mhc_2021.run(\"$INPUT_FILE\")"
