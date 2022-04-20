#!/bin/sh
set -euo pipefail

OUTPUT_DIR=$1

python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr1\", \"1\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr2\", \"2\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr3\", \"3\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr4\", \"4\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr5\", \"5\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr6\", \"6\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr7\", \"7\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr8\", \"8\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr9\", \"9\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr10\", \"10\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr11\", \"11\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr12\", \"12\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr13\", \"13\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr14\", \"14\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr15\", \"15\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr16\", \"16\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr17\", \"17\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr18\", \"18\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr19\", \"19\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr20\", \"20\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr21\", \"21\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chr22\", \"22\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chrX\", \"X\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chrY\", \"Y\")"
python manage.py shell -c "from scripts import gen_chromo_viz_level3; gen_chromo_viz_level3.run(\"$OUTPUT_DIR/level3_chrMT\", \"MT\")"
