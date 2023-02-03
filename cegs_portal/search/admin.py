from django.contrib import admin

from cegs_portal.search.models import (
    DNAFeature,
    Experiment,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)


class DNAFeatureAdmin(admin.ModelAdmin):
    raw_id_fields = ("closest_gene", "parent", "experiment_accession")
    list_display = ("accession_id", "feature_type", "public", "archived")
    search_fields = ["experiment__accession_id"]


admin.site.register(DNAFeature, DNAFeatureAdmin)


class ExperimentAdmin(admin.ModelAdmin):
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
