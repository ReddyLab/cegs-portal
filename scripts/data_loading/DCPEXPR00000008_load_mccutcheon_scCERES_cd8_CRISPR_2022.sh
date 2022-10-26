#!/bin/sh
INPUT_FILE=$1
FEATURES_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000008_load_mccutcheon_scCERES_cd8_CRISPR_2022; DCPEXPR00000008_load_mccutcheon_scCERES_cd8_CRISPR_2022.run(\"${INPUT_FILE}\", \"${FEATURES_FILE}\")"
