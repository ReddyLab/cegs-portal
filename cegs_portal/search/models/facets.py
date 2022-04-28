from enum import Enum

from django.db import models


class FacetType(Enum):
    DISCRETE = "Discrete"
    CONTINUOUS = "Continuous"


class Facet(models.Model):
    FACET_TYPE = [
        (FacetType.DISCRETE, FacetType.DISCRETE.value),
        (FacetType.CONTINUOUS, FacetType.CONTINUOUS.value),
    ]
    facet_type = models.CharField(
        max_length=30,
        choices=FACET_TYPE,
        default=FacetType.CONTINUOUS,
    )
    description = models.CharField(max_length=4096, null=True)
    name = models.CharField(max_length=256)


class FacetValue(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["value"], name="sfv_value_index"),
        ]

    value = models.CharField(max_length=30, null=True)
    facet = models.ForeignKey(Facet, on_delete=models.CASCADE, related_name="values")


class FacetedModel(models.Model):
    class Meta:
        abstract = True

    class Facets:
        pass

    facet_values = models.ManyToManyField(FacetValue)
    facet_num_values = models.JSONField(null=True)
