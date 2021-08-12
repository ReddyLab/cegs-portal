from django import forms


class UploadFileForm(forms.Form):
    dhs_file = forms.FileField(label="DHS File")
