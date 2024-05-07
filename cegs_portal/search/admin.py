import re

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from cegs_portal.search.models import (
    Analysis,
    DNAFeature,
    Experiment,
    Facet,
    FacetValue,
    File,
    Pipeline,
    RegulatoryEffectObservation,
)


def validate_ref_genome(value):
    if value != "" and not re.match(r"GRCh\d+(\.\d+)?", value):
        raise ValidationError(
            "%(ref)s is not a valid genome. Must be in the form of 'GRChXX' or 'GRChXX.Y' where Y is a patch level.",
            params={"ref": value},
        )


class DNAFeatureAdmin(admin.ModelAdmin):
    raw_id_fields = ("closest_gene", "parent", "experiment_accession")
    list_display = ("accession_id", "feature_type", "public", "archived")
    search_fields = ["experiment__accession_id"]


admin.site.register(DNAFeature, DNAFeatureAdmin)


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = (
            "filename",
            "description",
            "url",
            "experiment",
            "size",
            "category",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6, "columns": 90}),
        }


class FileAdmin(admin.ModelAdmin):
    form = FileForm
    list_display = ("truncate_filename", "experiment_name", "description")

    @admin.display(description="File Name")
    def truncate_filename(self, obj):
        filename = obj.filename
        if len(filename) <= 30:
            return filename

        return f"{filename[:15]}...{filename[-15:]}"

    @admin.display(description="Experiment")
    def experiment_name(self, obj):
        experiment = obj.experiment
        return obj.experiment.name if experiment is not None else "N/A"


admin.site.register(File, FileAdmin)


# StackedInline stackes the Experiment Data File fields vertically instead of horizontally(TabularInline).
# Extra  = 0 reduces repeat field sections
class FileInlineAdmin(admin.StackedInline):
    form = FileForm
    model = File
    extra = 0
    verbose_name = "File"

    @admin.display
    def other_file_info(self, obj):
        return f"{obj.filename}"


class ExperimentFacetValueInlineAdmin(admin.StackedInline):
    model = Experiment.facet_values.through
    extra = 0
    verbose_name = "Facet Value"

    @admin.display
    def facet_info(self, obj):
        return f"{obj.value} ({obj.facet.name})"


class ExperimentForm(forms.ModelForm):
    class Meta:
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6, "columns": 90}),
        }


class ExperimentAdmin(admin.ModelAdmin):
    form = ExperimentForm
    inlines = [ExperimentFacetValueInlineAdmin, FileInlineAdmin]
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


class PipelineForm(forms.ModelForm):
    class Meta:
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6, "columns": 90}),
        }


class PipelineInlineForm(admin.StackedInline):
    model = Pipeline
    form = PipelineForm
    extra = 0


class AnalysisFacetValueInlineAdmin(admin.StackedInline):
    model = Analysis.facet_values.through
    extra = 0
    verbose_name = "Facet Value"

    @admin.display
    def facet_info(self, obj):
        return f"{obj.value} ({obj.facet.name})"


class AnalysisForm(forms.ModelForm):
    verbose_name_plural = "Analyses"
    p_val_threshold = forms.FloatField(max_value=1.0, min_value=0.0, step_size=0.01, required=False)
    significance_measure = forms.CharField(max_length=2048, required=False)
    ref_genome = forms.CharField(max_length=10, validators=[validate_ref_genome], required=False)

    widgets = {
        "significance_measure": forms.Textarea(attrs={"rows": 6, "columns": 90}),
    }


class AnalysisAdmin(admin.ModelAdmin):
    form = AnalysisForm
    inlines = [AnalysisFacetValueInlineAdmin, PipelineInlineForm]
    list_display = (
        "accession_id",
        "description",
        "experiment_info",
    )
    fields = [
        "public",
        "archived",
        "accession_id",
        "description",
        "when",
    ]
    search_fields = ["experiment__accession_id", "experiment__name"]

    # TODO: This is definitely a cause of n+1 queries
    @admin.display(description="Experiment")
    def experiment_info(self, obj):
        exper = obj.experiment

        return f"{exper.accession_id}: {exper.description[:15]}..."

    @admin.display(description="Description")
    def description(self, obj):
        description = obj.description
        if len(description) <= 30:
            return description

        return f"{description[:30]}..."


admin.site.register(Analysis, AnalysisAdmin)


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
