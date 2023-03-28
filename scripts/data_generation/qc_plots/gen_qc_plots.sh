#!/bin/bash
set -euo pipefail

DATA_DIR=$1

# skip DCPEXPR00000001, it's not data we want to add

# DCPEXPR00000002
echo DCPEXPR00000002
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/vpdata.bin \
    --input ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -d ,
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/c_per_g.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/g_per_c.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/qqplot.bin \
    -p p_val \
    --uniform \
    -d , \
    -q 1000

# DCPEXPR00000003
echo DCPEXPR00000003
# python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/vpdata.bin \
#     --input ${DATA_DIR}/DCPEXPR00000003_klann_wgCERES_K562_2021/supplementary_table_13_DHS_summary_results.txt \
#     -x avg_logFC \
#     -y pValue \
#     -g geneSymbol
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/c_per_g.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000003_klann_wgCERES_K562_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/g_per_c.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000003_klann_wgCERES_K562_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000003_klann_wgCERES_K562_2021/supplementary_table_13_DHS_summary_results.txt \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/qqplot.bin \
    -p pValue \
    --uniform \
    --unlog-p-value \
    -q 1000

# DCPEXPR00000004
echo DCPEXPR00000004
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/vpdata.bin \
    --input ${DATA_DIR}/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/c_per_g.bin \
    --header \
    --input ${DATA_DIR}/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.run_negbinom.ncells_per_grna.txt \
    --bin-size 4
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/g_per_c.bin \
    --header \
    --input ${DATA_DIR}/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
    --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/qqplot.bin \
    -p p_val \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting \
    -q 1000

# DCPEXPR00000005
echo DCPEXPR00000005
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/vpdata.bin \
    --input ${DATA_DIR}/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/k562.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/c_per_g.bin \
    --header \
    --input ${DATA_DIR}/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/k562.run_negbinom.ncells_per_grna.txt \
    --bin-size 4
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/g_per_c.bin \
    --header \
    --input ${DATA_DIR}/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/k562.run_negbinom.ngrnas_per_cell.txt \
    --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/k562.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/qqplot.bin \
    -p p_val \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting \
    -q 1000

# DCPEXPR00000006
echo DCPEXPR00000006
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/vpdata.bin \
    --input ${DATA_DIR}/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/npc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/c_per_g.bin \
    --header \
    --input ${DATA_DIR}/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/npc.run_negbinom.ncells_per_grna.txt \
    --bin-size 4
python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/g_per_c.bin \
    --header \
    --input ${DATA_DIR}/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/npc.run_negbinom.ngrnas_per_cell.txt \
    --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/npc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/qqplot.bin \
    -p p_val \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting \
    -q 1000

# DCPEXPR00000007
echo DCPEXPR00000007
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000007/vpdata.bin \
    --input ${DATA_DIR}/DCPEXPR00000007_siklenka_atac-starr-seq_K562_2022/atacSTARR.ultra_deep.csaw.hg38.v10.common_file_formatted.txt \
    -x logFC \
    -y minusLog10PValue
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000007/c_per_g.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000007_siklenka_atac-starr-seq_K562_2022/npc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000007/g_per_c.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000007_siklenka_atac-starr-seq_K562_2022/npc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000007_siklenka_atac-starr-seq_K562_2022/atacSTARR.ultra_deep.csaw.hg38.v10.common_file_formatted.txt \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000007/qqplot.bin \
    -p minusLog10PValue \
    --unlog-p-value \
    --uniform \
    -q 1000

# DCPEXPR00000008
echo DCPEXPR00000008
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000008/vpdata.bin \
    --input ${DATA_DIR}/DCPEXPR00000008_mccutcheon_scCERES_cd8_CRISPRa_2022/crispra.mast.volcano.all.min_thres_4.with_coords.txt \
    -x avg_log2FC \
    -y p_val \
    -g target_gene
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000008/c_per_g.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000008_mccutcheon_scCERES_cd8_CRISPRa_2022/npc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000008/g_per_c.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000008_mccutcheon_scCERES_cd8_CRISPRa_2022/npc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000008_mccutcheon_scCERES_cd8_CRISPRa_2022/crispra.mast.volcano.all.min_thres_4.with_coords.txt \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000008/qqplot.bin \
    -p p_val \
    --uniform \
    -q 1000

# DCPEXPR00000009
echo DCPEXPR00000009
python3 ./scripts/data_generation/qc_plots/volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000009/vpdata.bin \
    --input ${DATA_DIR}/DCPEXPR00000009_mccutcheon_scCERES_cd8_CRISPRi_2022/crispri.mast.volcano.all.min_thres_4.with_coords.txt \
    -x avg_log2FC \
    -y p_val \
    -g target_gene
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000009/c_per_g.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000009_mccutcheon_scCERES_cd8_CRISPRi_2022/npc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 ./scripts/data_generation/qc_plots/histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000009/g_per_c.bin \
#     --header \
#     --input ${DATA_DIR}/DCPEXPR00000009_mccutcheon_scCERES_cd8_CRISPRi_2022/npc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 ./scripts/data_generation/qc_plots/qq_plot.py --input ${DATA_DIR}/DCPEXPR00000009_mccutcheon_scCERES_cd8_CRISPRi_2022/crispri.mast.volcano.all.min_thres_4.with_coords.txt \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000009/qqplot.bin \
    -p p_val \
    --uniform \
    -q 1000
