#!/bin/sh
INPUT_FILE=$1
GENOME=${2:-GRCh38}
PATCH=${3:-}

python manage.py shell -c "from scripts import load_gencode_gff3_data; load_gencode_gff3_data.run(\"$INPUT_FILE\", \"${GENOME}\", \"${PATCH}\")"
