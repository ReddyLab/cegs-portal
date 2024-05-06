import os
import struct

import numpy as np

from cegs_portal.get_expr_data.models import ReoSourcesTargets
from cegs_portal.search.models import Facet, FacetValue


def gen_qq_plot(analysis, analysis_dir):
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
    category_names = ["Targeting", "Controls"]

    x_axis_label = b"-log10(Theoretical p-value quantiles)"
    y_axis_label = b"-log10(Observed p-value quantiles)"

    reos = (
        ReoSourcesTargets.objects.filter(reo_analysis=analysis.accession_id)
        .order_by("reo_accession")
        .distinct("reo_accession")
        .values("cat_facets", "reo_facets")
    )

    qq_data = {0: [], 1: []}
    for reo in reos:
        p_val_log_10 = float(reo["reo_facets"]["-log10 Significance"])

        cat_facets = set(reo["cat_facets"])
        if cat_facets & non_ctrl:
            targeting_category = 0
        elif cat_facets & ctrl:
            targeting_category = 1
        else:
            targeting_category = 0

        qq_data[targeting_category].append(p_val_log_10)

    # If there is no data, drop that array
    keys = list(qq_data.keys())
    for key in keys:
        if len(qq_data[key]) == 0:
            del qq_data[key]

    sample_size = min([len(x) for x in qq_data.values()])

    quantile_count = min(10_000, sample_size)
    quantile_step = 1 / quantile_count
    percentiles = [x * quantile_step for x in range(1, 1 + quantile_count)]

    y_percentiles = [np.quantile(np.array(qq_data[category]), q=percentiles) for category in qq_data]

    s = sorted(np.random.uniform(0, 1, sample_size))
    x_percentiles = np.quantile(-np.log10(s), q=percentiles)

    p_val_percentiles = []
    for p in zip(x_percentiles, *y_percentiles):
        p_val_percentiles.extend(p)

    # The serialized format of the qqplot data is (using pythons `struct` module formats)
    #   (\d indicates a non-negative integer)
    #   See https://docs.python.org/3.11/library/struct.html#module-struct
    # >: Big-endian byte order
    # I: Quantile Count
    # B: Category count
    # Category Name list:
    #   B: Category name length
    #   \ds: Category name
    # B: X-axis label length
    # \ds: X-axis label
    # B: Y-axis label length
    # \ds: Y-axis label
    # \df: quantile values. These are packed together like, x0yyx1yyx2yyx3yy, etc.
    #     Where "x" a value from the uniform quantile and each "y" is from an observed data quantile
    #     for a particular category. The "y" values are in the same order as the category names.
    y_val_name_format = [f"B{len(category_names[idx])}s" for idx in qq_data]

    y_val_name_data = []
    for idx in qq_data:
        y_val_name_data.extend((len(category_names[idx]), category_names[idx].encode("utf-8")))

    packing_list = f">IB{''.join(y_val_name_format)}B{len(x_axis_label)}sB{len(y_axis_label)}s{(1 + len(qq_data)) * quantile_count}f"
    out_filename = os.path.join(analysis_dir, "qqplot.pd")
    with open(out_filename, "wb") as out_file:
        out_file.write(
            struct.pack(
                packing_list,
                quantile_count,
                len(qq_data),  # category count
                *y_val_name_data,
                len(x_axis_label),
                x_axis_label,
                len(y_axis_label),
                y_axis_label,
                *p_val_percentiles,
            )
        )
