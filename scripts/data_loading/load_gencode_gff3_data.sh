#!/bin/bash
INPUT_FILE=$1
ACCESSION_FILE=$2
GENOME=${3:-GRCh38}
PATCH=${4:-}
VERSION=${5:0}

python manage.py shell -c "from scripts.data_loading import load_gencode_gff3_data; load_gencode_gff3_data.run(\"$INPUT_FILE\", \"${ACCESSION_FILE}\", \"${GENOME}\", \"${PATCH}\", \"${VERSION}\")"
