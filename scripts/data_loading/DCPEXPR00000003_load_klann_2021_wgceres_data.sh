#!/bin/sh
INPUT_FILE=$1
ACCESSION_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000003_load_klann_2021_wgceres_data; DCPEXPR00000003_load_klann_2021_wgceres_data.run(\"${INPUT_FILE}\", \"${ACCESSION_FILE}\")"
