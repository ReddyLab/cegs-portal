#!/bin/sh
set -euo pipefail

INPUT_FILE=$1
EXPERIMENT_ACCESSION=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000002_dhs_closest_ccres_klann_2021_scceres; DCPEXPR0000000002_dhs_closest_ccres_klann_2021_scceres.run(\"${INPUT_FILE}\", \"${EXPERIMENT_ACCESSION}\")"
