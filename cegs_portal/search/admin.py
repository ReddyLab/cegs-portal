import re

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from cegs_portal.search.models import (
    Analysis,
    DNAFeature,
    Experiment,
    ExperimentCollection,
    ExperimentRelation,
    ExperimentSource,
    Facet,
    FacetValue,
    File,
    Pipeline,
    RegulatoryEffectObservation,
)


def validate_genome_assembly(value):
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
    url = forms.URLField(
        label="URL",
        required=False,
        max_length=200,
        widget=forms.URLInput(attrs={"class": "vURLField"}),
        assume_scheme="http",
    )

    class Meta:
        model = File
        fields = (
            "filename",
            "description",
            "url",
            "location",
            "experiment",
            "analysis",
            "size",
            "category",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


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
    list_select_related = ["facet"]

    @admin.display
    def facet_info(self, obj):
        return f"{obj.value} ({obj.facet.name})"


class ExperimentRelationForm(forms.ModelForm):
    class Meta:
        model = ExperimentRelation
        fields = (
            "other_experiment",
            "description",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


class ExperimentRelationInlineAdmin(admin.StackedInline):
    form = ExperimentRelationForm
    model = Experiment.related_experiments.through
    extra = 0
    verbose_name = "Related Experiment"
    fk_name = "this_experiment"


class ExperimentSourceInlineAdmin(admin.StackedInline):
    model = ExperimentSource
    min_num = 1
    max_num = 1
    verbose_name = "Experiment Attribution"

    @admin.display
    def source_info(self, obj):
        lab = f", {obj.lab}" if obj.lab else ""
        return f"{obj.pi}{lab}"


class ExperimentForm(forms.ModelForm):
    class Meta:
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6, "columns": 90}),
        }


class ExperimentAdmin(admin.ModelAdmin):
    form = ExperimentForm
    inlines = [
        ExperimentSourceInlineAdmin,
        ExperimentFacetValueInlineAdmin,
        FileInlineAdmin,
        ExperimentRelationInlineAdmin,
    ]
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

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        obj.save(update_access=True)


admin.site.register(Experiment, ExperimentAdmin)


class ExperimentCollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


admin.site.register(ExperimentCollection, ExperimentCollectionAdmin)


class ExperimentRelationAdmin(admin.ModelAdmin):
    list_display = ("from_experiment", "to_experiment")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("this_experiment", "other_experiment")


admin.site.register(ExperimentRelation, ExperimentRelationAdmin)

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
    p_value_threshold = forms.FloatField(max_value=1.0, min_value=0.0, step_size=0.01)
    p_value_adj_method = forms.CharField(max_length=128, empty_value="unknown")
    genome_assembly = forms.CharField(max_length=20, validators=[validate_genome_assembly])
    genome_assembly_patch = forms.CharField(max_length=10, required=False)


class AnalysisAdmin(admin.ModelAdmin):
    form = AnalysisForm
    inlines = [AnalysisFacetValueInlineAdmin]
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
        "genome_assembly",
        "genome_assembly_patch",
        "p_value_threshold",
        "p_value_adj_method",
        "when",
    ]
    search_fields = ["experiment__accession_id", "experiment__name"]

    # TODO: This is definitely a cause of n+1 queries
    @admin.display(description="Experiment")
    def experiment_info(self, obj):
        expr = obj.experiment
        desc = expr.description[:15] if expr.description is not None else None

        return f"{expr.accession_id}: {expr.name}{' - ' + desc if desc is not None else ''}..."

    @admin.display(description="Description")
    def description(self, obj):
        description = obj.description
        if len(description) <= 30:
            return description

        return f"{description[:30]}..."

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        obj.save(update_access=True)


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
