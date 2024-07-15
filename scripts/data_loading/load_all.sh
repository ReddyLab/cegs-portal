#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=$1

START_TIME=`date`

# Load facets
echo "Load facets"
./scripts/data_loading/load_facets.sh ${DATA_DIR}/facets/facets.tsv

# Delete indexes for faster data loading
python manage.py shell -c "from scripts.data_loading.db import drop_indexes; drop_indexes()"

# Load gencode annotations and FeatureAssemblies (genes, transcripts, exons)
./scripts/data_loading/load_gencode_gff3_data.sh ${DATA_DIR}/gencode_annotations/gencode.v19.annotation.gff3 hg19 '' 19
./scripts/data_loading/load_gencode_gff3_data.sh ${DATA_DIR}/gencode_annotations/gencode.v43.annotation.gff3 hg38 13 43

# Load cCREs from SCREEN
echo "Load SCREEN cCREs"
./scripts/data_loading/load_screen_ccres.sh ${DATA_DIR}/screen_ccres/ccres_hg19.json GRCh37 ''
./scripts/data_loading/load_screen_ccres.sh ${DATA_DIR}/screen_ccres/ccres_hg38.json GRCh38 13

# Rebuild indexes so experiment data loading doesn't take forever.
python manage.py shell -c "from scripts.data_loading.db import create_indexes; create_indexes()"

# Load experiment data
./scripts/data_loading/DCPEXPR0000000002_load_klann_2021_scceres_data.sh ${DATA_DIR}

./scripts/data_loading/DCPEXPR0000000003_load_klann_2021_wgceres_data.sh ${DATA_DIR}

./scripts/data_loading/DCPEXPR0000000004_load_bounds_scCERES_mhc_2021.sh ${DATA_DIR}
./scripts/data_loading/DCPEXPR0000000005_load_bounds_scCERES_mhc_2021.sh ${DATA_DIR}
./scripts/data_loading/DCPEXPR0000000006_load_bounds_scCERES_mhc_2021.sh ${DATA_DIR}

./scripts/data_loading/DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022.sh ${DATA_DIR}

./scripts/data_loading/DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPRa_2022.sh ${DATA_DIR}
./scripts/data_loading/DCPEXPR0000000009_load_mccutcheon_scCERES_cd8_CRISPRi_2022.sh ${DATA_DIR}

echo "Started: ${START_TIME}"
echo "Finished: $(date)"
