from django.db import models


class Facet(models.Model):
    description = models.CharField(max_length=4096, null=True)
    name = models.CharField(max_length=256)


class FacetValue(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["value"], name="sfv_value_index"),
        ]

    value = models.CharField(max_length=30)
    facet = models.ForeignKey(Facet, on_delete=models.CASCADE, related_name="values")


class FacetedModel(models.Model):
    class Meta:
        abstract = True

    facet_values = models.ManyToManyField(FacetValue)
