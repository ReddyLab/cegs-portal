from django import forms
from django.contrib import admin

from cegs_portal.search.models import (
    DNAFeature,
    Experiment,
    ExperimentDataFile,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
    File,
)


class DNAFeatureAdmin(admin.ModelAdmin):
    raw_id_fields = ("closest_gene", "parent", "experiment_accession")
    list_display = ("accession_id", "feature_type", "public", "archived")
    search_fields = ["experiment__accession_id"]


admin.site.register(DNAFeature, DNAFeatureAdmin)


class OtherFileForm(forms.ModelForm):
    pass
    # class Meta:
    #     widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


class ExperimentFacetValueForm(forms.ModelForm):
    pass
    # class Meta:
    #     widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


class ExperimentDataFileForm(forms.ModelForm):
    class Meta:
        widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


class ExperimentForm(forms.ModelForm):
    class Meta:
        widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


# StackedInline stackes the Experiment Data File fields vertically instead of horizontally(TubularInline).
# Extra  = 0 reduces repeat field sections
class ExperimentDataFileInlineAdmin(admin.StackedInline):
    form = ExperimentDataFileForm
    model = ExperimentDataFile
    extra = 0


class OtherFileInlineAdmin(admin.StackedInline):
    form = OtherFileForm
    model = Experiment.other_files.through
    extra = 0
    verbose_name = "Other File"

    @admin.display
    def other_file_info(self, obj):
        return f"{obj.filename}"


admin.site.register(File)


class ExperimentFacetValueInlineAdmin(admin.StackedInline):
    form = ExperimentFacetValueForm
    model = Experiment.facet_values.through
    extra = 0
    verbose_name = "Facet Value"

    @admin.display
    def facet_info(self, obj):
        return f"{obj.value} ({obj.facet.name})"


class ExperimentAdmin(admin.ModelAdmin):
    form = ExperimentForm
    inlines = [ExperimentDataFileInlineAdmin, ExperimentFacetValueInlineAdmin, OtherFileInlineAdmin]
    fields = [
        "public",
        "archived",
        "accession_id",
        "name",
        "description",
        "experiment_type",
        "biosamples",
    ]
    list_display = ("accession_id", "name", "public", "archived")
    list_filter = ["public", "archived"]
    search_fields = ["name", "description"]


admin.site.register(Experiment, ExperimentAdmin)


admin.site.register(Facet)


class FacetValueAdmin(admin.ModelAdmin):
    search_fields = ["value", "facet__name"]
    list_display = ["facet_list_display"]

    @admin.display
    def facet_list_display(self, obj):
        return f"{obj.value} ({obj.facet.name})"


admin.site.register(FacetValue, FacetValueAdmin)


class RegEffectAdmin(admin.ModelAdmin):
    raw_id_fields = ("sources", "targets", "experiment_accession")
    list_display = ("accession_id", "experiment", "public", "archived")
    search_fields = ["experiment__accession_id"]


admin.site.register(RegulatoryEffectObservation, RegEffectAdmin)
