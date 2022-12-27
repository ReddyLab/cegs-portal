from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation
from cegs_portal.uploads.forms import UploadFileForm


def upload(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES["dhs_file"])
            return HttpResponseRedirect(reverse("uploads:upload_complete"))
    else:
        form = UploadFileForm()
    return render(request, "uploads/upload.html", {"form": form})


def upload_complete(request):
    return render(request, "uploads/upload_complete.html", {})


#  Don't actually use this right now
def handle_uploaded_file(file):
    for line in file:
        cell_line, chrom, start, end, _name, _direction, _effect_size = line.decode("utf-8").split(", ")

        # skip header
        if cell_line == "cell_line":
            continue

        dhs = DNAFeature(
            chrom_name=chrom,
            location=NumericRange(int(start), int(end)),
            cell_line=cell_line,
        )
        # dhs.save()

        re = RegulatoryEffectObservation(sources=[dhs])
        re.save()
