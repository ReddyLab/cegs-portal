from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Fieldset, Layout, Submit
from django import forms

from cegs_portal.uploads.validators import validate_experiment_accession_id


class UploadFileForm(forms.Form):
    experiment_accession = forms.CharField(
        label="Experiment Accession ID", max_length=17, validators=[validate_experiment_accession_id]
    )
    experiment_file = forms.FileField(label="Experiment File", required=False)
    experiment_url = forms.URLField(label="Experiment URL", required=False, assume_scheme="http")
    analysis_file = forms.FileField(label="Analysis File", required=False)
    analysis_url = forms.URLField(label="Analysis URL", required=False, assume_scheme="http")

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.form_action = "uploads:upload"
        helper.attrs = {"enctype": "multipart/form-data"}
        helper.layout = Layout(
            Fieldset(
                '<legend class="form-header-text">Upload Experiment and/or Analysis Metadata</legend>',
                HTML('<div class="title-separator my-3.5"></div>'),
                "experiment_accession",
                Fieldset(
                    '<div class="form-label">Experiment Metadata</div>',
                    Field("experiment_url", wrapper_class="indent"),
                    Field("experiment_file", wrapper_class="indent inline_url_field"),
                ),
                Fieldset(
                    '<div class="form-label">Analysis Metadata</div>',
                    Field("analysis_url", wrapper_class="indent"),
                    Field("analysis_file", wrapper_class="indent inline_url_field"),
                ),
            ),
            Submit("submit", "Upload"),
        )

        return helper
