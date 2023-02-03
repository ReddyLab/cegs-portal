from django import forms
from django.contrib import admin
from django.db import models
from django.forms import Textarea

from cegs_portal.search.models import (
    DNAFeature,
    Experiment,
    ExperimentDataFile,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)


class DNAFeatureAdmin(admin.ModelAdmin):
    raw_id_fields = ("closest_gene", "parent", "experiment_accession")
    list_display = ("accession_id", "feature_type", "public", "archived")
    search_fields = ["experiment__accession_id"]


admin.site.register(DNAFeature, DNAFeatureAdmin)


class ExperimentForm(forms.ModelForm):
    class Meta:
        widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


# StackedInline stackes the Experiment Data File fields vertically instead of horizontally(TubularInline).
# Extra  = 0 reduces repeat field sections
class ExperimentDataFileInlineAdmin(admin.StackedInline):
    form = ExperimentForm
    model = ExperimentDataFile
    extra = 0


class ExperimentAdmin(admin.ModelAdmin):
    form = ExperimentForm
    inlines = [ExperimentDataFile]
    raw_id_fields = ["facet_values"]
    fields = [
        "public",
        "archived",
        "accession_id",
        "name",
        "description",
        "experiment_type",
        "facet_values",
        "biosamples",
        "other_files",
    ]
    list_display = ("accession_id", "name", "public", "archived")
    list_filter = ["public", "archived"]
    search_fields = ["name", "description"]


admin.site.register(Experiment, ExperimentAdmin)


admin.site.register(Facet)


class FacetValueAdmin(admin.ModelAdmin):
    search_fields = ["value", "facet__name"]


admin.site.register(FacetValue, FacetValueAdmin)


class RegEffectAdmin(admin.ModelAdmin):
    raw_id_fields = ("sources", "targets", "experiment_accession")
    list_display = ("accession_id", "experiment", "public", "archived")
    search_fields = ["experiment__accession_id"]


admin.site.register(RegulatoryEffectObservation, RegEffectAdmin)
