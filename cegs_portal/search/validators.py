from re import fullmatch

from django.core.exceptions import ValidationError


def validate_analysis_accession_id(value):
    if value is not None and fullmatch("DCPAN[A-F0-9]{8,10}", value) is None:
        raise ValidationError(
            f"""{value} is not of the form "DCPANXXXXXXXX" where X is a hexadecimal digit (0-9, A-F)"""
        )
