#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=$1

# skip DCPEXPR0000000001, it's not data we want to add

# DCPEXPR0000000002
echo DCPEXPR0000000002
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000002/vpdata.pd \
    --input ${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -d ,
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000002/c_per_g.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000002/g_per_c.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000002/qqplot.pd \
    -p p_val \
    --log-p-value \
    -d , \
    -q 10_000

# DCPEXPR0000000003
echo DCPEXPR0000000003
# python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000003/vpdata.pd \
#     --input ${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/supplementary_table_5_DHS_summary_results.tsv \
#     -x avg_logFC \
#     -y pValue \
#     -g geneSymbol
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000003/c_per_g.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000003/g_per_c.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/supplementary_table_5_DHS_summary_results.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000003/qqplot.pd \
    -p pValue \
    -q 10_000

# DCPEXPR0000000004
echo DCPEXPR0000000004
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000004/vpdata.pd \
    --input ${DATA_DIR}/DCPEXPR0000000004_bounds_scCERES_mhc_ipsc_2021/ipsc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000004/c_per_g.pd \
    --header \
    --input ${DATA_DIR}/DCPEXPR0000000004_bounds_scCERES_mhc_ipsc_2021/ipsc.run_negbinom.ncells_per_grna.txt \
    --bin-size 4
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000004/g_per_c.pd \
    --header \
    --input ${DATA_DIR}/DCPEXPR0000000004_bounds_scCERES_mhc_ipsc_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
    --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000004_bounds_scCERES_mhc_ipsc_2021/ipsc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000004/qqplot.pd \
    -p p_val \
    --log-p-value \
    --category-column type \
    --categories targeting nontargeting \
    --category-names Targeting "Non-targeting" \
    -q 10_000

# DCPEXPR0000000005
echo DCPEXPR0000000005
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000005/vpdata.pd \
    --input ${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/k562.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000005/c_per_g.pd \
    --header \
    --input ${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/k562.run_negbinom.ncells_per_grna.txt \
    --bin-size 4
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000005/g_per_c.pd \
    --header \
    --input ${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/k562.run_negbinom.ngrnas_per_cell.txt \
    --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/k562.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000005/qqplot.pd \
    -p p_val \
    --log-p-value \
    --category-column type \
    --categories targeting nontargeting \
    --category-names Targeting "Non-targeting" \
    -q 10_000

# DCPEXPR0000000006
echo DCPEXPR0000000006
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000006/vpdata.pd \
    --input ${DATA_DIR}/DCPEXPR0000000006_bounds_scCERES_mhc_npc_2021/npc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000006/c_per_g.pd \
    --header \
    --input ${DATA_DIR}/DCPEXPR0000000006_bounds_scCERES_mhc_npc_2021/npc.run_negbinom.ncells_per_grna.txt \
    --bin-size 4
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000006/g_per_c.pd \
    --header \
    --input ${DATA_DIR}/DCPEXPR0000000006_bounds_scCERES_mhc_npc_2021/npc.run_negbinom.ngrnas_per_cell.txt \
    --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000006_bounds_scCERES_mhc_npc_2021/npc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000006/qqplot.pd \
    -p p_val \
    --log-p-value \
    --category-column type \
    --categories targeting nontargeting \
    --category-names Targeting "Non-targeting" \
    -q 10_000

# DCPEXPR0000000007
echo DCPEXPR0000000007
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000007/vpdata.pd \
    --input ${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/atacSTARR.ultra_deep.csaw.hg38.v10.common_file_formatted.tsv \
    -x logFC \
    -y minusLog10PValue
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000007/c_per_g.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/npc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000007/g_per_c.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/npc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/atacSTARR.ultra_deep.csaw.hg38.v10.common_file_formatted.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000007/qqplot.pd \
    -p minusLog10PValue \
    -q 10_000

# DCPEXPR0000000008
echo DCPEXPR0000000008
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000008/vpdata.pd \
    --input ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/crispra.mast.volcano.all.min_thres_4.with_coords.tsv \
    -x avg_log2FC \
    -y p_val \
    -g target_gene
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000008/c_per_g.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/npc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000008/g_per_c.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/npc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/crispra.mast.volcano.all.min_thres_4.with_coords.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000008/qqplot.pd \
    -p p_val \
    --log-p-value \
    -q 10_000

# DCPEXPR0000000009
echo DCPEXPR0000000009
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000009/vpdata.pd \
    --input ${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/crispri.mast.volcano.all.min_thres_4.with_coords.tsv \
    -x avg_log2FC \
    -y p_val \
    -g target_gene
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000009/c_per_g.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/npc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000009/g_per_c.pd \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/npc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/crispri.mast.volcano.all.min_thres_4.with_coords.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR0000000009/qqplot.pd \
    -p p_val \
    --log-p-value \
    -q 10_000
