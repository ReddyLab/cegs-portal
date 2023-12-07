#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=$1

# Load facets
echo "Load facets"
./scripts/data_loading/load_facets.sh ${DATA_DIR}/facets/facets.tsv

python manage.py shell -c "from scripts.data_loading.db import drop_indexes; drop_indexes()"
# Load gencode annotations and FeatureAssemblies (genes, transcripts, exons)
./scripts/data_loading/load_gencode_gff3_data.sh ${DATA_DIR}/gencode_annotations/gencode.v19.annotation.gff3 GRCh37 '' 19
./scripts/data_loading/load_gencode_gff3_data.sh ${DATA_DIR}/gencode_annotations/gencode.v43.annotation.gff3 GRCh38 13 43

# Load cCREs from SCREEN
echo "Load SCREEN cCREs"
./scripts/data_loading/load_screen_ccres.sh ${DATA_DIR}/screen_ccres/ccres_hg19.json GRCh37 ''
./scripts/data_loading/load_screen_ccres.sh ${DATA_DIR}/screen_ccres/ccres_hg38.json GRCh38 13
python manage.py shell -c "from scripts.data_loading.db import create_indexes; create_indexes()"

# Load experiment data
# Just leave this experiment out from now on. It's been superceded by DCPEXPR4-6
# echo DCPEXPR0000000001
# ./scripts/data_loading/DCPEXPR0000000001_load_bounds_2021_scceres_data.sh ${DATA_DIR}/DCPEXPR0000000001_bounds_scCERES_iPSC_2021/experiment.json ${DATA_DIR}/DCPEXPR0000000001_bounds_scCERES_iPSC_2021/analysis001.json

./scripts/data_loading/DCPEXPR0000000002_load_klann_2021_scceres_data.sh ${DATA_DIR}

./scripts/data_loading/DCPEXPR0000000003_load_klann_2021_wgceres_data.sh ${DATA_DIR}

./scripts/data_loading/DCPEXPR0000000004_load_bounds_scCERES_mhc_2021.sh ${DATA_DIR}
./scripts/data_loading/DCPEXPR0000000005_load_bounds_scCERES_mhc_2021.sh ${DATA_DIR}
./scripts/data_loading/DCPEXPR0000000006_load_bounds_scCERES_mhc_2021.sh ${DATA_DIR}

./scripts/data_loading/DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022.sh ${DATA_DIR}

echo DCPEXPR0000000008
./scripts/data_loading/DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022.sh ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/experiment.json \
  ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/analysis001.json \
  ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/features.tsv
echo DCPEXPR0000000009
./scripts/data_loading/DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022.sh ${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/experiment.json \
  ${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/analysis001.json \
  ${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/features.tsv

python manage.py shell -c "from cegs_portal.get_expr_data.models import ReoSourcesTargets; ReoSourcesTargets.refresh_view()"
python manage.py shell -c "from cegs_portal.get_expr_data.models import ReoSourcesTargetsSigOnly; ReoSourcesTargetsSigOnly.refresh_view()"
