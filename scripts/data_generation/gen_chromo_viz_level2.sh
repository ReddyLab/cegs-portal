#!/bin/sh
set -euo pipefail

EXPERIMENT=$1
OUTPUT_DIR=$2

python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"1\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"2\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"3\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"4\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"5\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"6\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"7\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"8\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"9\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"10\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"11\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"12\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"13\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"14\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"15\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"16\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"17\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"18\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"19\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"20\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"21\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"22\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"X\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"Y\")"
python manage.py shell -c "from scripts.data_generation import gen_chromo_viz_level2; gen_chromo_viz_level2.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"MT\")"
