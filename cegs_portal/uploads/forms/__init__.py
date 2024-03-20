from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from cegs_portal.uploads.validators import validate_experiment_accession_id


class UploadFileForm(forms.Form):
    experiment_accession = forms.CharField(
        label="Experiment Accession ID", max_length=17, validators=[validate_experiment_accession_id]
    )
    experiment_file = forms.FileField(label="Experiment File", required=False)
    analysis_file = forms.FileField(label="Analysis File", required=False)

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.form_action = "uploads:upload"
        helper.attrs = {"enctype": "multipart/form-data"}
        helper.add_input(Submit("submit", "Upload"))
        return helper
