import argparse
import csv
import struct

from scipy.stats import norm, uniform
from scipy.stats.mstats import mquantiles


def process(args):
    p_val_col = args.p_value_column
    unlog = args.unlog_p_value

    quantile_count = int(args.quantile_count)

    quantile_step = 1 / quantile_count
    percentiles = [x * quantile_step for x in range(1, 1 + quantile_count)]

    csv_reader = csv.DictReader(args.input, delimiter=args.delimiter)
    x_label = b"Non-Control Quantiles"

    if args.control_column is not None:
        y_label = b"Control Quantiles"
        control_col = args.control_column
        control_val = args.control_value
        non_control_val = args.non_control_value
        x_values = []
        y_values = []
        for row in csv_reader:
            p_val = float(row[p_val_col])
            if unlog:
                p_val = 10 ** (-p_val)
            if row[control_col] == control_val:
                x_values.append(p_val)
            elif row[control_col] == non_control_val:
                y_values.append(p_val)

        x_percentiles = mquantiles(x_values, percentiles)
    else:
        y_values = []
        for row in csv_reader:
            p_val = float(row[p_val_col])
            y_values.append(p_val)

        if args.normal:
            x_percentiles = norm.ppf(percentiles, loc=0.5, scale=0.15)
            y_label = b"Theoretical Normal Quantiles"
        elif args.uniform:
            x_percentiles = uniform.ppf(percentiles)
            y_label = b"Theoretical Uniform Quantiles"

    y_percentiles = mquantiles(y_values, percentiles)

    # print(f'[{", ".join(str({"c": x, "nc": y}) for x, y in zip(x_percentiles, y_percentiles))}]')

    p_val_percentiles = []
    for p in zip(x_percentiles, y_percentiles):
        p_val_percentiles.extend(p)

    args.output.write(
        struct.pack(
            f">IB{len(x_label)}sB{len(y_label)}s{2 * quantile_count}f",
            quantile_count,
            len(x_label),
            x_label,
            len(y_label),
            y_label,
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
        "--unlog-p-value",
        help="run 10**-(p-value) because p-value in data is really -log10(p-value)",
        action="store_true",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--control-column")
    parser.add_argument("--control-value", help="Required if --control-column is set")
    parser.add_argument("--non-control-value", help="Required if --control-column is set")
    group.add_argument("--normal", help="Compare data to a normal distribution", action="store_true")
    group.add_argument("--uniform", help="Compare data to a uniform distribution", action="store_true")
    parser.add_argument("-d", "--delimiter", default="\t")
    parser.add_argument("-q", "--quantile-count", default=100)

    return parser.parse_args()


if __name__ == "__main__":
    process(parse_args())
