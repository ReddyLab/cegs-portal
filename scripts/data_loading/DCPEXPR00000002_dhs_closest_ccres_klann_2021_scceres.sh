#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000002_dhs_closest_ccres_klann_2021_scceres; DCPEXPR00000002_dhs_closest_ccres_klann_2021_scceres.run(\"${INPUT_FILE}\")"
