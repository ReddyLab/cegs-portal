from django import forms


class SearchForm(forms.Form):
    query = forms.CharField(label="Search", initial="HLA-A")


class SearchGeneForm(forms.Form):
    query = forms.CharField(label="Search", initial="HLA-A")


class SearchLocationForm(forms.Form):
    query = forms.CharField(label="Search", initial="chr11:33858576 - 33892076")
