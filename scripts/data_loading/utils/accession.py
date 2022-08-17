import csv
from enum import Enum


class AccessionId:
    def __init__(self, id_string, prefix="DCP", id_length=8):
        self.id_string = id_string
        self.prefix = "DCP"
        self.id_length = 8
        self.abbrev = id_string[len(prefix) : len(id_string) - id_length]  # noqa E203
        self.id_num = int(id_string[len(id_string) - id_length :], 16)  # noqa E203

    def __str__(self) -> str:
        return f"{self.prefix}{self.abbrev}{self.id_num:08X}"

    def __eq__(self, other) -> bool:
        return (
            self.id_string == other.id_string
            and self.prefix == other.prefix
            and self.id_length == other.id_length
            and self.abbrev == other.abbrev
            and self.id_num == other.id_num
        )

    def incr(self):
        self.id_num += 1

    def decr(self):
        self.id_num -= 1


class AccessionType(Enum):
    GENE = "gene"
    TRANSCRIPT = "transcript"
    EXON = "exon"
    REGULATORY_EFFECT = "regulatory effect"
    GRNA = "grna"
    CCRE = "ccre"
    DHS = "dhs"
    EXPERIMENT = "experiment"


class AccessionIds:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.header = []
        self.id_dict = {}
        self._load_data()

    def _load_data(self):
        with open(self.file_path, newline="") as accession_id_file:
            accession_ids = csv.reader(accession_id_file, delimiter="\t")

            self.header = accession_ids.__next__()  # Skip the header
            for key, id_string in accession_ids:
                self.id_dict[AccessionType(key)] = AccessionId(id_string)

    def write(self, file_path=None):
        if file_path is None:
            file_path = self.file_path

        with open(file_path, "w", newline="") as accession_id_file:
            id_writer = csv.writer(accession_id_file, delimiter="\t")
            id_writer.writerow(["type", "id"])
            for key, acc_id in self.id_dict.items():
                id_writer.writerow([key.value, str(acc_id)])

    def incr(self, key: AccessionType):
        old_value = str(self.id_dict[key])
        self.id_dict[key].incr()
        return old_value

    def decr(self, key: AccessionType):
        old_value = str(self.id_dict[key])
        self.id_dict[key].decr()
        return old_value

    def set(self, key, accession_id):
        self.id_dict[key] = accession_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write()
