import csv
import sys


def run(data_filename, output_filename):
    with open(data_filename) as data_file, open(output_filename, "w") as output_file:
        reader = csv.DictReader(data_file)
        for row in reader:
            output_file.write(f"{row['dhs_chrom']}\t{row['dhs_start']}\t{row['dhs_end']}\n")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
