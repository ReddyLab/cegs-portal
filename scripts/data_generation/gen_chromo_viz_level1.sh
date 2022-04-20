#!/bin/sh
set -euo pipefail

OUTPUT_FILE=$1

python manage.py shell -c "from scripts import gen_chromo_viz_level1; gen_chromo_viz_level1.run(\"$OUTPUT_FILE\", 2_000_000)"
