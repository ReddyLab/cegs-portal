from re import fullmatch

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_gene_ids(gene_ids):
    if not isinstance(gene_ids, dict):
        raise ValidationError(
            _("%(gene_ids)s is not a dictionary"),
            params={"gene_ids": gene_ids},
        )

    valid_keys = {"ucsc", "ensembl", "hgnc", "havana"}
    for key, value in gene_ids.items():
        if key not in valid_keys:
            raise ValidationError(
                _("%(key)s is a valid gene id source"),
                params={"key": key},
            )
        if not isinstance(value, str):
            raise ValidationError(
                _("%(value)s is not a string"),
                params={"value": value},
            )


def validate_accession_id(value):
    if value is not None and fullmatch("DCP[A-Z]{0,4}[0-9A-F]{8}", value) is None:
        raise ValidationError(
            f"""{value} is not of the form "DCPYYYYXXXXXXXX", where Ys are capital
            letters indicating the type of object, and X is a hexadecimal digit (0-9, A-F)"""
        )
