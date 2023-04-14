import argparse
import csv
import struct
from statistics import mean, median


class KeyedCounter:
    def __init__(self, key_func=lambda x: x):
        self.storage = {}
        self.key_func = key_func

    def insert(self, item):
        bucket = self.key_func(item)
        if bucket in self.storage:
            self.storage[bucket] += 1
        else:
            self.storage[bucket] = 1

    def __getitem__(self, key):
        return self.storage.get(key, 0)


def process(args):
    csv_reader = csv.reader(args.input, delimiter=" ")
    counter = KeyedCounter(key_func=lambda x: x // args.bin_size)

    if args.header:
        next(csv_reader)

    all_numbers = []
    for _, number in csv_reader:
        number = int(number)
        all_numbers.append(number)
        counter.insert(number)

    all_numbers.sort()

    max_number = all_numbers[-1]
    bucket_amounts = [counter[i] for i in range((max_number // args.bin_size) + 1)]

    # The serialized format of the histogram data is (using pythons `struct` module formats)
    #   (\d indicates a non-negative integer)
    #   See https://docs.python.org/3.11/library/struct.html#module-struct
    # >: Big-endian byte order
    # I: The size of each histogram bin
    # f: The mean of the histogram
    # f: The median of the histogram
    # I: The number of bins
    # \dI: The values for each bin
    args.output.write(
        struct.pack(
            f">IffI{len(bucket_amounts)}I",
            args.bin_size,
            mean(all_numbers),
            median(all_numbers),
            len(bucket_amounts),
            *bucket_amounts,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser(
        prog="HistogramData",
        description="Extract data for histograms into a binary format.",
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
    parser.add_argument("-b", "--bin-size", type=int, default=10)
    parser.add_argument("--header", help="Indicate if file has header", action="store_true")

    return parser.parse_args()


if __name__ == "__main__":
    process(parse_args())
