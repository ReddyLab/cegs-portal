#!/bin/sh
set -euo pipefail

DATA_DIR=$1

EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/analysis001.json
CLOSEST_CCRE_FILE=${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/closest_ccres.txt

echo "Loading DCPEXPR0000000005"

# generate ccre overlaps
./scripts/data_generation/ccre_overlaps.sh \
    ${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/k562.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    ${DATA_DIR}/screen_ccres/GRCh38-cCREs.bed \
    grna.chr grna.start grna.end \
    ${CLOSEST_CCRE_FILE}

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_experiment; DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_experiment.run(\"${EXPERIMENT_FILE}\", \"${CLOSEST_CCRE_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_analysis; DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_analysis.run(\"${ANALYSIS_FILE}\")"

rm ${CLOSEST_CCRE_FILE}
