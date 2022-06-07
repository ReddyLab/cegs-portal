#!/bin/sh
set -euo pipefail

EXPERIMENT=$1
GENOME=$2
OUTPUT_DIR=$3

python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"1\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"2\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"3\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"4\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"5\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"6\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"7\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"8\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"9\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"10\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"11\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"12\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"13\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"14\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"15\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"16\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"17\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"18\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"19\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"20\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"21\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"22\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"X\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"Y\", \"$GENOME\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"MT\", \"$GENOME\")"
