from enum import Enum

from django.db import models


class DNAFeatureType(Enum):
    GENE = "Gene"
    TRANSCRIPT = "Transcript"
    EXON = "Exon"
    CCRE = "cCRE"
    DHS = "DHS"
    GRNA = "gRNA"
    CAR = "Chromatin Accessible Region"
    CRE = "Called Regulatory Element"
    GE = "Genomic Element"

    @property
    def accession_abbreviation(self) -> str:
        match self:
            case DNAFeatureType.GENE:
                return "GENE"
            case DNAFeatureType.TRANSCRIPT:
                return "T"
            case DNAFeatureType.EXON:
                return "EXON"
            case DNAFeatureType.CCRE:
                return "CCRE"
            case DNAFeatureType.DHS:
                return "DHS"
            case DNAFeatureType.GRNA:
                return "GRNA"
            case DNAFeatureType.CAR:
                return "CAR"
            case DNAFeatureType.CRE:
                return "CRE"
            case DNAFeatureType.GE:
                return "GE"
            case _:
                raise ValueError(f"No accession abbreviation defined for {self}")

    @classmethod
    def from_db_str(cls, db_str):
        match db_str:
            case "DNAFeatureType.GENE":
                return DNAFeatureType.GENE
            case "DNAFeatureType.TRANSCRIPT":
                return DNAFeatureType.TRANSCRIPT
            case "DNAFeatureType.EXON":
                return DNAFeatureType.EXON
            case "DNAFeatureType.CCRE":
                return DNAFeatureType.CCRE
            case "DNAFeatureType.DHS":
                return DNAFeatureType.DHS
            case "DNAFeatureType.GRNA":
                return DNAFeatureType.GRNA
            case "DNAFeatureType.CAR":
                return DNAFeatureType.CAR
            case "DNAFeatureType.CRE":
                return DNAFeatureType.CRE
            case "DNAFeatureType.GE":
                return DNAFeatureType.GE
            case _:
                raise ValueError(f"No feature type defined for {db_str}")


class DNAFeatureSourceType(models.TextChoices):
    CCRE = "CCRE", DNAFeatureType.CCRE.value
    DHS = "DHS", DNAFeatureType.DHS.value
    GRNA = "GRNA", DNAFeatureType.GRNA.value
    CAR = "CAR", DNAFeatureType.CAR.value
    CRE = "CRE", DNAFeatureType.CRE.value
    GE = "GE", DNAFeatureType.GE.value
