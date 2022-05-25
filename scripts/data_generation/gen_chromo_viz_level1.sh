#!/bin/sh
set -euo pipefail

EXPERIMENT=$1
OUTPUT_FILE=$2

python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level1; gen_chromo_viz_level1.run(\"$OUTPUT_FILE\", \"$EXPERIMENT\", 2_000_000)"
