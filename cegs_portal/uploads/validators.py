from re import fullmatch

from django.core.exceptions import ValidationError


def validate_experiment_accession_id(value):
    if value is None or fullmatch("DCPEXPR[0-9A-F]{10}", value) is None:
        raise ValidationError(
            f"""{value} is not of the form "DCPEXPRXXXXXXXX" where X is a hexadecimal digit (0-9, A-F)"""
        )
