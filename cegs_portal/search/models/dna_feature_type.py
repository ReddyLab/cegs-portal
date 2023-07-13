from enum import Enum

from django.db import models


class DNAFeatureType(Enum):
    GENE = "Gene"
    TRANSCRIPT = "Transcript"
    EXON = "Exon"
    CCRE = "cCRE"
    DHS = "DHS"
    GRNA = "gRNA"
    CAR = "Chromatin Accessable Region"

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
            case _:
                raise Exception(f"No accession abbreviation defined for {self}")


class DNAFeatureSourceType(models.TextChoices):
    CCRE = "CCRE", "cCRE"
    DHS = "DHS", "DHS"
    GRNA = "GRNA", "gRNA"
    CAR = "CAR", "CAR"
