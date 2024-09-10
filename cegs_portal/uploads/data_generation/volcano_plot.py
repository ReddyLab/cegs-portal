import os
import struct

from cegs_portal.get_expr_data.models import ReoSourcesTargets
from cegs_portal.search.models import (
    DNAFeature,
    Facet,
    FacetValue,
    GrnaType,
    RegulatoryEffectObservation,
)


def gen_volcano_plot(analysis, analysis_dir):
    ctrl_facet = Facet.objects.get(name=DNAFeature.Facet.GRNA_TYPE.value)
    targeting_facet = FacetValue.objects.filter(facet=ctrl_facet, value=GrnaType.TARGETING.value).values_list(
        "id", flat=True
    )[0]
    pos_ctrl_facet = FacetValue.objects.filter(facet=ctrl_facet, value=GrnaType.POSITIVE_CONTROL.value).values_list(
        "id", flat=True
    )[0]
    neg_ctrl_facet = FacetValue.objects.filter(facet=ctrl_facet, value=GrnaType.NEGATIVE_CONTROL.value).values_list(
        "id", flat=True
    )[0]
    non_ctrl = {targeting_facet}
    ctrl = {pos_ctrl_facet, neg_ctrl_facet}

    sig_threshold = analysis.p_value_threshold

    reos = (
        ReoSourcesTargets.objects.filter(reo_analysis=analysis.accession_id)
        .order_by("reo_accession")
        .distinct("reo_accession")
        .values("reo_facets", "target_gene_symbol", "cat_facets")
    )

    out_filename = os.path.join(analysis_dir, "vpdata.pd")
    with open(out_filename, "wb") as out_file:
        for reo in reos:
            try:
                reo_facets = reo["reo_facets"]
                p_val = float(reo_facets[RegulatoryEffectObservation.Facet.SIGNIFICANCE.value])
                p_val_log_10 = float(reo_facets[RegulatoryEffectObservation.Facet.LOG_SIGNIFICANCE.value])
                avg_log_fc = float(reo_facets[RegulatoryEffectObservation.Facet.EFFECT_SIZE.value])

                # Skip non-significant, low fold-change data
                # This is by far most of the data so this keeps the number of
                # observation relatively small, which means the output file is small
                if p_val > sig_threshold and abs(avg_log_fc) < 1:
                    continue

                if reo["target_gene_symbol"] is not None:
                    symbol = reo["target_gene_symbol"].encode("utf-8")
                else:
                    symbol = b""

                cat_facets = set(reo["cat_facets"])
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
                    p_val_log_10,
                    avg_log_fc,
                    targeting_category,
                    len(symbol),
                    symbol,
                )

                out_file.write(data)
            except Exception as ex:
                print(reo)
                raise ex
