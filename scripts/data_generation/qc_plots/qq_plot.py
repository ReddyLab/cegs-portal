import argparse
import struct
import sys

import numpy as np
import pandas as pd


def process(args):
    p_val_col = args.p_value_column
    log = args.log_p_value
    quantile_count = args.quantile_count
    categories = args.categories
    category_names = args.category_names

    quantile_step = 1 / quantile_count
    percentiles = [x * quantile_step for x in range(1, 1 + quantile_count)]
    qq_data = pd.read_csv(args.input, sep=args.delimiter, index_col=False, dtype_backend="pyarrow")

    x_axis_label = b"-log10(Theoretical p-value quantiles)"
    y_axis_label = b"-log10(Observed p-value quantiles)"
    if args.category_column is not None:
        sample_size = min(qq_data.loc[qq_data[args.category_column] == category].shape[0] for category in categories)
        y_values = {
            category: qq_data.loc[qq_data[args.category_column] == category, p_val_col] for category in categories
        }
    else:
        sample_size = qq_data.shape[0]
        y_values = {category: qq_data[p_val_col] for category in categories}

    if log:
        for category in categories:
            # A RuntimeWarning will get thrown by the -np.log10 code here if temp_y has an 0.0 values.
            # -np.log10(0) is Infinity, which we don't want, so we clamp it down to 10% higher than the
            # largest non-infinity value.

            temp_y = y_values[category]
            log_temp_y = -np.log10(temp_y)
            log_min_y = -np.log10(temp_y[temp_y > 0].min())
            log_temp_y[temp_y == 0.0] = log_min_y * 1.1
            y_values[category] = log_temp_y

    y_percentiles = [np.quantile(y_values[category], q=percentiles) for category in categories]

    s = sorted(np.random.uniform(0, 1, sample_size))
    if log:
        x_percentiles = np.quantile(-np.log10(s), q=percentiles)
    else:
        x_percentiles = np.quantile(s, q=percentiles)

    p_val_percentiles = []
    for p in zip(x_percentiles, *y_percentiles):
        p_val_percentiles.extend(p)

    y_val_name_format = [f"B{len(category_name)}s" for category_name in category_names]
    y_val_name_data = []
    for category_name in category_names:
        y_val_name_data.extend((len(category_name), category_name.encode("utf-8")))
    args.output.write(
        struct.pack(
            f">IB{''.join(y_val_name_format)}B{len(x_axis_label)}s"
            f"B{len(y_axis_label)}s{(1 + len(y_values)) * quantile_count}f",
            quantile_count,
            len(y_values),  # y value count
            *y_val_name_data,
            len(x_axis_label),
            x_axis_label,
            len(y_axis_label),
            y_axis_label,
            *p_val_percentiles,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser(
        prog="QQPlotData",
        description="Extract data for QQ Plots into a binary format.",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output file",
        type=argparse.FileType("wb"),
        required=True,
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Input file",
        type=argparse.FileType("r"),
        required=True,
    )
    parser.add_argument("-p", "--p-value-column", required=True)
    parser.add_argument(
        "--log-p-value",
        help="run -log10(p-value)",
        action="store_true",
    )
    parser.add_argument("-c", "--category-column")
    parser.add_argument("-a", "--categories", help="A list of categories to use", nargs="+", default=["targeting"])
    parser.add_argument(
        "-n", "--category-names", help="A list of display names of categories to use", nargs="+", default=["Targeting"]
    )
    parser.add_argument("-d", "--delimiter", default="\t")
    parser.add_argument("-q", "--quantile-count", type=int, default=1000)

    args = parser.parse_args()

    if len(args.categories) != len(args.category_names):
        print("Category list and category name list must be the same length", file=sys.stderr)
        sys.exit(-1)

    return args


if __name__ == "__main__":
    process(parse_args())
