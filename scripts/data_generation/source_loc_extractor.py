import argparse
import csv

from utils.misc import get_delimiter


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=argparse.FileType("r"), required=True)
    parser.add_argument("-o", "--output", type=argparse.FileType("w"), required=True)
    parser.add_argument("--chr_name_col", required=True)
    parser.add_argument("--chr_start_col", required=True)
    parser.add_argument("--chr_end_col", required=True)

    return parser.parse_args()


def run(data_file, output_file, chr_name_col, chr_start_col, chr_end_col):
    if chr_name_col.isnumeric() and chr_start_col.isnumeric() and chr_end_col.isnumeric():
        reader = csv.reader(data_file, delimiter=get_delimiter(data_file.name))
        chr_name_col = int(chr_name_col)
        chr_start_col = int(chr_start_col)
        chr_end_col = int(chr_end_col)
    else:
        reader = csv.DictReader(data_file, delimiter=get_delimiter(data_file.name))
    for row in reader:
        output_file.write(f"{row[chr_name_col]}\t{row[chr_start_col]}\t{row[chr_end_col]}\n")


if __name__ == "__main__":
    args = get_args()
    run(args.input, args.output, args.chr_name_col, args.chr_start_col, args.chr_end_col)
