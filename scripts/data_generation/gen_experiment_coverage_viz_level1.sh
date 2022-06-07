#!/bin/sh
set -euo pipefail

EXPERIMENT=$1
GENOME=$2
OUTPUT_FILE=$3

python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_FILE\", \"$EXPERIMENT\", \"$GENOME\")"
