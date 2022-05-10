from re import fullmatch

from django.core.exceptions import ValidationError
from django.db import models


def validate_accession_id(value):
    if value is not None and fullmatch("DCP[A-Z][0-9A-Z]{8}", value) is None:
        raise ValidationError(
            f"""{value} is not of the form "DCPYXXXXXXXX", where Y is a capital
            letter indicating the type of object, and X is a number or capital letter"""
        )


class Accessioned(models.Model):
    class Meta:
        abstract = True

    class Facets:
        pass

    accession_id = models.CharField(max_length=12, validators=[validate_accession_id], null=True, unique=True)
