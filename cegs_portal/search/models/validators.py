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
