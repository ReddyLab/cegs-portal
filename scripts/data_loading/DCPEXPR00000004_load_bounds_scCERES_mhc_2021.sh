#!/bin/sh
INPUT_FILE=$1
ACCESSION_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000004_load_bounds_scCERES_mhc_2021; DCPEXPR00000004_load_bounds_scCERES_mhc_2021.run(\"${INPUT_FILE}\", \"${ACCESSION_FILE}\")"
