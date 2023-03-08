import argparse
import csv
import struct

from scipy.stats.mstats import mquantiles


def process(args):
    p_val_col = args.p_value_column
    control_col = args.control_column
    control_val = args.control_value
    non_control_val = args.non_control_value
    quantile_count = int(args.quantile_count)

    quantile_step = 1 / quantile_count
    percentiles = [x * quantile_step for x in range(1, 1 + quantile_count)]

    csv_reader = csv.DictReader(args.input, delimiter=args.delimiter)

    control_p_values = []
    non_control_p_values = []
    for row in csv_reader:
        p_val = float(row[p_val_col])
        if row[control_col] == control_val:
            control_p_values.append(p_val)
        elif row[control_col] == non_control_val:
            non_control_p_values.append(p_val)

    control_percentiles = mquantiles(control_p_values, percentiles)
    non_control_percentiles = mquantiles(non_control_p_values, percentiles)

    # print(
    #     f'[{", ".join(str({"c": str(x), "nc": str(y)})
    # for x, y in zip(control_percentiles, non_control_percentiles))}]'
    # )

    p_val_percentiles = []
    for p in zip(control_percentiles, non_control_percentiles):
        p_val_percentiles.extend(p)

    args.output.write(
        struct.pack(
            f">{2 * quantile_count}f",
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
    parser.add_argument("-c", "--control-column", required=True)
    parser.add_argument("--control-value", required=True)
    parser.add_argument("--non-control-value", required=True)
    parser.add_argument("-d", "--delimiter", default="\t")
    parser.add_argument("-q", "--quantile-count", default=100)

    return parser.parse_args()


if __name__ == "__main__":
    process(parse_args())
