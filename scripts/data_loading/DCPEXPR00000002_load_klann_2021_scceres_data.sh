#!/bin/sh
INPUT_FILE=$1
ACCESSION_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000002_load_klann_2021_scceres_data; DCPEXPR00000002_load_klann_2021_scceres_data.run(\"${INPUT_FILE}\", \"${ACCESSION_FILE}\")"