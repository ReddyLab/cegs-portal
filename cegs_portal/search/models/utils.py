from enum import Enum, auto
from typing import Optional

from psycopg2.extras import NumericRange


class AccessionType(Enum):
    GENE = "gene"
    TRANSCRIPT = "transcript"
    EXON = "exon"
    REGULATORY_EFFECT_OBS = "regulatory effect observation"
    GRNA = "grna"
    CCRE = "ccre"
    DHS = "dhs"
    EXPERIMENT = "experiment"
    CAR = "chromatin accessable region"
    TT = "tissue type"
    CL = "cell line"
    BIOS = "biosample"

    def abbrev(self):
        if self == AccessionType.GENE:
            return "GENE"
        elif self == AccessionType.TRANSCRIPT:
            return "T"
        elif self == AccessionType.EXON:
            return "EXON"
        elif self == AccessionType.REGULATORY_EFFECT_OBS:
            return "REO"
        elif self == AccessionType.GRNA:
            return "GRNA"
        elif self == AccessionType.CCRE:
            return "CCRE"
        elif self == AccessionType.DHS:
            return "DHS"
        elif self == AccessionType.EXPERIMENT:
            return "EXPR"
        elif self == AccessionType.CAR:
            return "CAR"
        elif self == AccessionType.TT:
            return "TT"
        elif self == AccessionType.CL:
            return "CL"
        elif self == AccessionType.BIOS:
            return "BIOS"
        else:
            raise Exception("Invalid Accession type")


class AccessionId:
    id_string: str
    prefix: str
    id_length: int
    abbrev: str
    id_num: int

    def __init__(self, id_string: str, prefix: str = "DCP", id_length: int = 8):
        self.id_string = id_string
        self.prefix = prefix
        self.id_length = id_length
        self.abbrev = id_string[len(prefix) : len(id_string) - id_length]  # noqa E203
        self.id_num = int(id_string[len(id_string) - id_length :], 16)  # noqa E203

    def __str__(self) -> str:
        return f"{self.prefix}{self.abbrev}{self.id_num:08X}"

    def __eq__(self, other: "AccessionId") -> bool:
        return (
            self.id_string == other.id_string
            and self.prefix == other.prefix
            and self.id_length == other.id_length
            and self.abbrev == other.abbrev
            and self.id_num == other.id_num
        )

    def incr(self):
        self.id_num += 1

    @classmethod
    def start_id(cls, accession_type: AccessionType, prefix: str = "DCP", id_length: int = 8):
        return AccessionId(f"{prefix}{accession_type.abbrev()}{'0' * id_length}")


class QueryToken(Enum):
    ENSEMBL_ID = auto()
    ACCESSION_ID = auto()
    GENE_NAME = auto()

    def associate(self, value: str) -> tuple["QueryToken", str]:
        return (self, value)


class ChromosomeLocation:
    def __init__(self, chromo: str, start: str, end: Optional[str] = None):
        self.chromo = chromo
        if end is None:
            self.range = NumericRange(int(start), int(start), bounds="[]")
        else:
            self.range = NumericRange(int(start), int(end))

    def __str__(self) -> str:
        return f"{self.chromo}: {self.range.lower}-{self.range.upper}"

    def __eq__(self, other) -> bool:
        return self.chromo == other.chromo and self.range == other.range

    def __repr__(self) -> str:
        return self.__str__()
