#!/usr/bin/env bash
INPUT_FILE=$1
GENOME=${2:-GRCh38}
PATCH=${3:-}
VERSION=${4:0}

python manage.py shell -c "from scripts.data_loading import load_gencode_gff3_data; load_gencode_gff3_data.run(\"$INPUT_FILE\", \"${GENOME}\", \"${PATCH}\", \"${VERSION}\")"
