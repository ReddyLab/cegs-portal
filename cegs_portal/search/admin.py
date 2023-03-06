import re

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from cegs_portal.search.models import (
    DNAFeature,
    Experiment,
    ExperimentDataFileInfo,
    Facet,
    FacetValue,
    File,
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
    p_val_threshold = forms.FloatField(max_value=1.0, min_value=0.0, step_size=0.01, required=False)
    significance_measure = forms.CharField(max_length=2048, required=False)
    ref_genome = forms.CharField(max_length=10, validators=[validate_ref_genome], required=False)

    class Meta:
        model = File
        fields = (
            "filename",
            "description",
            "url",
            "experiment",
            "size",
            "category",
            "p_val_threshold",
            "significance_measure",
            "ref_genome",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6, "columns": 90}),
            "significance_measure": forms.Textarea(attrs={"rows": 6, "columns": 90}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data_file_info = self.instance.data_file_info
        if data_file_info is not None:
            self.fields["p_val_threshold"].initial = data_file_info.p_value_threshold
            self.fields["significance_measure"].initial = data_file_info.significance_measure
            ref_genome = data_file_info.ref_genome
            ref_genome_patch = data_file_info.ref_genome_patch
            if ref_genome != "":
                if ref_genome_patch is not None and ref_genome_patch != "":
                    self.fields["ref_genome"].initial = f"{ref_genome}.{ref_genome_patch}"
                else:
                    self.fields["ref_genome"].initial = data_file_info.ref_genome

    def clean(self):
        p_val_threshold = self.cleaned_data["p_val_threshold"]
        significance_measure = self.cleaned_data["significance_measure"]
        ref_genome_full = self.cleaned_data["ref_genome"]
        if not (
            all(((p_val_threshold == "" or p_val_threshold is None), significance_measure == "", ref_genome_full == ""))
            or all((p_val_threshold != "", significance_measure != "", ref_genome_full != ""))
        ):
            raise ValidationError(
                "Must specify either all of (p val threshold, significance measure, ref genome) or none of them"
            )
        return super().clean()

    def save(self, commit=True):
        p_val_threshold = self.cleaned_data["p_val_threshold"]
        significance_measure = self.cleaned_data["significance_measure"]
        ref_genome_full = self.cleaned_data["ref_genome"]
        ref_genome_parts = ref_genome_full.split(".")
        ref_genome = ref_genome_parts[0]
        ref_genome_patch = "" if len(ref_genome_parts) == 1 else ref_genome_parts[1]

        if (p_val_threshold == "" or p_val_threshold is None) and significance_measure == "" and ref_genome_full == "":
            if self.instance.data_file_info is not None:
                self.instance.data_file_info.delete()
                self.instance.data_file_info = None
        else:
            if self.instance.data_file_info is not None:
                self.instance.data_file_info.p_value_threshold = p_val_threshold
                self.instance.data_file_info.significance_measure = significance_measure
                self.instance.data_file_info.ref_genome = ref_genome
                self.instance.data_file_info.ref_genome_patch = ref_genome_patch
                self.instance.data_file_info.save()
            else:
                data_file_info = ExperimentDataFileInfo(
                    p_value_threshold=p_val_threshold,
                    significance_measure=significance_measure,
                )
                data_file_info.ref_genome = ref_genome
                data_file_info.ref_genome_patch = ref_genome_patch
                data_file_info.save()
                self.instance.data_file_info = data_file_info
        return super().save(commit)


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


# StackedInline stackes the Experiment Data File fields vertically instead of horizontally(TubularInline).
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
        widgets = {"description": forms.Textarea(attrs={"rows": 6, "columns": 90})}


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
