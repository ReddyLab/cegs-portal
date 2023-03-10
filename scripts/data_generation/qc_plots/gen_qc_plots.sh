#!/bin/bash
set -euo pipefail

# DCPEXPR00000002
python3 volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/vpdata.bin \
    --input ~/Documents/ccgr_portal/data/DCPEXPR00000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -d ,
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/c_per_g.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000002_klann_scCERES_K562_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/g_per_c.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000002_klann_scCERES_K562_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 qq_plot.py --input ~/Documents/ccgr_portal/data/DCPEXPR00000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000002/qqplot.bin \
    -p pval_fdr_corrected \
    --normal \
    -d , \
    -q 1000


# DCPEXPR00000003
python3 volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/vpdata.bin \
    --input ~/Documents/ccgr_portal/data/DCPEXPR00000003_klann_wgCERES_K562_2021/supplementary_table_5_DHS_summary_results.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/c_per_g.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000003_klann_wgCERES_K562_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/g_per_c.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000003_klann_wgCERES_K562_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 qq_plot.py --input ~/Documents/ccgr_portal/data/DCPEXPR00000003_klann_wgCERES_K562_2021/supplementary_table_5_DHS_summary_results.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000003/qqplot.bin \
    -p pval_fdr_corrected \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting \
    -d , \
    -q 1000

# DCPEXPR00000004
python3 volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/vpdata.bin \
    --input ~/Documents/ccgr_portal/data/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/c_per_g.bin \
    --header \
    --input ~/Documents/ccgr_portal/data/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.run_negbinom.ncells_per_grna.txt \
    --bin-size 4
python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/g_per_c.bin \
    --header \
    --input ~/Documents/ccgr_portal/data/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
    --bin-size 1
python3 qq_plot.py --input ~/Documents/ccgr_portal/data/DCPEXPR00000004_bounds_scCERES_mhc_ipsc_2021/ipsc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000004/qqplot.bin \
    -p pval_fdr_corrected \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting \
    -q 1000

# DCPEXPR00000005
python3 volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/vpdata.bin \
    --input ~/Documents/ccgr_portal/data/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/k562.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/c_per_g.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/g_per_c.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 qq_plot.py --input ~/Documents/ccgr_portal/data/DCPEXPR00000005_bounds_scCERES_mhc_k562_2021/k562.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000005/qqplot.bin \
    -p pval_fdr_corrected \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting \
    -q 1000

# DCPEXPR00000006
python3 volcano_plot.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/vpdata.bin \
    --input ~/Documents/ccgr_portal/data/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/npc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    -x avg_logFC \
    -y pval_fdr_corrected \
    -g gene_symbol \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/c_per_g.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/ipsc.run_negbinom.ncells_per_grna.txt \
#     --bin-size 4
# python3 histogram.py --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/g_per_c.bin \
#     --header \
#     --input ~/Documents/ccgr_portal/data/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/ipsc.run_negbinom.ngrnas_per_cell.txt \
#     --bin-size 1
python3 qq_plot.py --input ~/Documents/ccgr_portal/data/DCPEXPR00000006_bounds_scCERES_mhc_npc_2021/npc.expect_cells.grna.de.markers.MAST.annotatedfull.final.update20220117.LRB.tsv \
    --output ./cegs_portal/static_data/search/experiments/DCPEXPR00000006/qqplot.bin \
    -p pval_fdr_corrected \
    -c type \
    --control-value nontargeting \
    --non-control-value targeting \
    -q 1000
