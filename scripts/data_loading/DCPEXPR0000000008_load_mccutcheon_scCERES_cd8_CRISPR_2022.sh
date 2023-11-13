#!/bin/sh
EXPERIMENT_FILE=$1
ANALYSIS_FILE=$2
FEATURES_FILE=$3

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_experiment; DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_analysis; DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_analysis.run(\"${ANALYSIS_FILE}\", \"${FEATURES_FILE}\")"
