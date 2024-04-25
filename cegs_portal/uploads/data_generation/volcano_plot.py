import os
import struct

from cegs_portal.get_expr_data.models import ReoSourcesTargets
from cegs_portal.search.models import Facet, FacetValue


def gen_volcano_plot(analysis, analysis_dir):
    ctrl_facet = Facet.objects.get(name="gRNA Type")
    targeting_facet = FacetValue.objects.filter(facet=ctrl_facet, value="Targeting").values_list("id", flat=True)[0]
    pos_ctrl_facet = FacetValue.objects.filter(facet=ctrl_facet, value="Positive Control").values_list("id", flat=True)[
        0
    ]
    neg_ctrl_facet = FacetValue.objects.filter(facet=ctrl_facet, value="Negative Control").values_list("id", flat=True)[
        0
    ]
    non_ctrl = {targeting_facet}
    ctrl = {pos_ctrl_facet, neg_ctrl_facet}

    results = analysis.files.all()[0].data_file_info
    sig_threshold = results.p_value_threshold

    reos = ReoSourcesTargets.objects.filter(reo_analysis=analysis.accession_id)

    out_filename = os.path.join(analysis_dir, "vpdata.pd")
    with open(out_filename, "wb") as out_file:
        for reo in reos:
            try:
                p_val = float(reo.reo_facets["-log10 Significance"])
                avg_log_fc = float(reo.reo_facets["Effect Size"])

                # Skip non-significant, low fold-change data
                # This is by far most of the data so this keeps the number of
                # observation relatively small, which means the output file is small
                if p_val > sig_threshold and abs(avg_log_fc) < 1:
                    continue

                symbol = reo.target_gene_symbol.encode("utf-8")

                cat_facets = set(reo.cat_facets)
                if cat_facets & non_ctrl:
                    targeting_category = 0
                elif cat_facets & ctrl:
                    targeting_category = 1
                else:
                    targeting_category = 0

                # The serialized format of the histogram data is (using pythons `struct` module formats)
                #   (\d indicates a non-negative integer)
                #   See https://docs.python.org/3.11/library/struct.html#module-struct
                # >: Big-endian byte order
                # f: -log10(p-value)
                # f: avg log fold change
                # B: A number associated with the category the data come from ("targeting", "nontargeting", etc.)
                # B: The length of the associated gene symbol
                # \ds: The gene symbol

                data = struct.pack(
                    f">ffBB{len(symbol)}s",
                    p_val,
                    avg_log_fc,
                    targeting_category,
                    len(symbol),
                    symbol,
                )

                out_file.write(data)
            except Exception as ex:
                print(reo)
                raise ex
