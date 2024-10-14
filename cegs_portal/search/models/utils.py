from enum import Enum, StrEnum
from typing import Optional

from psycopg.types.range import Int4Range

from .dna_feature_type import DNAFeatureType


class AccessionType(Enum):
    GENE = "gene"
    TRANSCRIPT = "transcript"
    EXON = "exon"
    REGULATORY_EFFECT_OBS = "regulatory effect observation"
    GRNA = "grna"
    CCRE = "ccre"
    DHS = "dhs"
    EXPERIMENT = "experiment"
    CAR = "chromatin accessible region"
    CRE = "called regulatory element"
    TT = "tissue type"
    CL = "cell line"
    BIOS = "biosample"
    ANALYSIS = "analysis"

    def abbrev(self):
        if self == AccessionType.GENE:
            return "GENE"
        if self == AccessionType.TRANSCRIPT:
            return "T"
        if self == AccessionType.EXON:
            return "EXON"
        if self == AccessionType.REGULATORY_EFFECT_OBS:
            return "REO"
        if self == AccessionType.GRNA:
            return "GRNA"
        if self == AccessionType.CCRE:
            return "CCRE"
        if self == AccessionType.DHS:
            return "DHS"
        if self == AccessionType.EXPERIMENT:
            return "EXPR"
        if self == AccessionType.CAR:
            return "CAR"
        if self == AccessionType.CRE:
            return "CRE"
        if self == AccessionType.TT:
            return "TT"
        if self == AccessionType.CL:
            return "CL"
        if self == AccessionType.BIOS:
            return "BIOS"
        if self == AccessionType.ANALYSIS:
            return "AN"

        raise Exception(f"Invalid Accession type: {self}")

    @classmethod
    def from_feature_type(cls, feature_type):
        match feature_type:
            case DNAFeatureType.GENE.value:
                return AccessionType.GENE
            case DNAFeatureType.TRANSCRIPT.value:
                return AccessionType.TRANSCRIPT
            case DNAFeatureType.EXON.value:
                return AccessionType.EXON
            case DNAFeatureType.CCRE.value:
                return AccessionType.CCRE
            case DNAFeatureType.DHS.value:
                return AccessionType.DHS
            case DNAFeatureType.GRNA.value:
                return AccessionType.GRNA
            case DNAFeatureType.CAR.value:
                return AccessionType.CAR
            case DNAFeatureType.CRE.value:
                return AccessionType.CRE

        raise Exception(f"Invalid DNAFeatureType: {feature_type}")


class AccessionId:
    id_string: str
    prefix: str
    prefix_length: int
    id_num_length: int
    abbrev: str
    id_num: int

    def __init__(self, id_string: str, prefix_length: int = 3, id_num_length: int = 10):
        self.id_string = id_string
        self.prefix = id_string[0:prefix_length]
        self.prefix_length = prefix_length
        self.id_num_length = id_num_length
        self.abbrev = id_string[prefix_length : len(id_string) - id_num_length]  # noqa E203
        self.id_num = int(id_string[len(id_string) - id_num_length :], 16)  # noqa E203

    def __str__(self) -> str:
        return f"{self.prefix}{self.abbrev}{self.id_num:0{self.id_num_length}X}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AccessionId) and not isinstance(other, str):
            return NotImplemented
        return str(self) == str(other)

    def incr(self):
        self.id_num += 1

    @classmethod
    def start_id(cls, accession_type: AccessionType, prefix: str = "DCP", id_num_length: int = 10) -> "AccessionId":
        return AccessionId(
            f"{prefix}{accession_type.abbrev()}{'0' * id_num_length}",
            prefix_length=len(prefix),
            id_num_length=id_num_length,
        )


class IdType(StrEnum):
    ENSEMBL = "ensembl"
    ACCESSION = "accession"
    GENE_NAME = "name"

    def associate(self, value: str) -> tuple["IdType", str]:
        return (self, value)


class ChromosomeLocation:
    def __init__(self, chromo: str, start: str | int, end: Optional[str | int] = None):
        self.chromo = chromo
        if end is None:
            self.range = Int4Range(int(start), int(start), bounds="[]")
        else:
            self.range = Int4Range(int(start), int(end))

    def __str__(self) -> str:
        return f"{self.chromo}: {self.range.lower}-{self.range.upper}"

    def __eq__(self, other) -> bool:
        return self.chromo == other.chromo and self.range == other.range

    def __repr__(self) -> str:
        return self.__str__()
