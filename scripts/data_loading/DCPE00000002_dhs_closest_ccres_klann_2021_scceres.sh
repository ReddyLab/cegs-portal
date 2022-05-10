#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts.data_loading import DCPE00000002_dhs_closest_ccres_klann_2021_scceres; DCPE00000002_dhs_closest_ccres_klann_2021_scceres.run(\"$INPUT_FILE\")"
