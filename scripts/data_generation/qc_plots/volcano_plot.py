import argparse
import csv
import math
import struct


def process(args):
    sig_threshold = args.significance_threshold
    fold_change_col = args.fold_change_column
    p_val_col = args.p_value_column
    gene_sym_col = args.gene_symbol_column
    if args.control_column is not None:
        control_col = args.control_column
        control_val = args.control_value
        non_control_val = args.non_control_value
        valid_types = {non_control_val: 0, control_val: 1}
    else:
        control_col = None
        control_val = None
        non_control_val = None

    csv_reader = csv.DictReader(args.input, delimiter=args.delimiter)

    # Calculate the minimum p value. This will be used to generate a suitable
    # -log10 p value for entries that have a p value of 0
    old_vals = None
    min_p_val = 1
    for row in csv_reader:
        # skip duplicate rows. These rows only differ by "dhs_overlaps_genebody_gene",
        # which doesn't matter for our purposes
        if gene_sym_col is not None and (row[p_val_col], row[gene_sym_col]) == old_vals:
            continue

        # skip rows of non-recognized guide types
        if control_col is not None and not row[control_col] in valid_types:
            continue

        if gene_sym_col is not None:
            old_vals = (row[p_val_col], row[gene_sym_col])

        p_val = float(row[p_val_col])
        if p_val < min_p_val and p_val != 0:
            min_p_val = p_val

    args.input.seek(0)  # "rewind" the file
    csv_reader = csv.DictReader(args.input, delimiter=args.delimiter)
    max_log10_p_val = -math.log10(min_p_val) * args.max_pval_factor
    old_vals = None
    for row in csv_reader:
        # skip duplicate rows. These rows only differ by "dhs_overlaps_genebody_gene",
        # which doesn't matter for our purposes
        if gene_sym_col is not None and (row[p_val_col], row[gene_sym_col]) == old_vals:
            continue

        # skip rows of non-recognized guide types
        if control_col is not None and not row[control_col] in valid_types:
            continue

        if gene_sym_col is not None:
            old_vals = (row[p_val_col], row[gene_sym_col])

        try:
            p_val = float(row[p_val_col])
            avg_log_fc = float(row[fold_change_col])

            # Skip non-significant, low fold-change data
            # This is by far most of the data so this keeps the number of
            # observation relatively small, which means the output file is small
            if p_val > sig_threshold and abs(avg_log_fc) < 1:
                continue

            if p_val == 0:
                neg_log_10_p_val = max_log10_p_val
            else:
                neg_log_10_p_val = -math.log10(p_val)

            if gene_sym_col is not None:
                symbol = row[gene_sym_col].encode("utf-8")
            else:
                symbol = b""

            args.output.write(
                struct.pack(
                    f">ffBB{len(symbol)}s",
                    neg_log_10_p_val,
                    avg_log_fc,
                    0 if control_col is None else valid_types[row[control_col]],
                    len(symbol),
                    symbol,
                )
            )
        except Exception as ex:
            print(row)
            raise ex


def parse_args():
    parser = argparse.ArgumentParser(
        prog="VolcanoPlotData",
        description="Extract data for volcano plots into a binary format",
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
    parser.add_argument("-x", "--fold-change-column", required=True)
    parser.add_argument("-y", "--p-value-column", required=True)
    parser.add_argument("-g", "--gene-symbol-column")
    parser.add_argument(
        "-s",
        "--significance-threshold",
        type=float,
        default=0.05,
        help="The maxium p-value considered for ",
    )
    parser.add_argument("-c", "--control-column")
    parser.add_argument("--control-value", help="Required if --control-column is set")
    parser.add_argument("--non-control-value", help="Required if --control-column is set")
    parser.add_argument(
        "--max-pval-factor",
        help="How much larger than -log10(max p-val) -log10(0) should be considered",
        default=1.1,
        type=float,
    )
    parser.add_argument("-d", "--delimiter", default="\t")

    return parser.parse_args()


if __name__ == "__main__":
    process(parse_args())
