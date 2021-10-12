from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNaseIHypersensitiveSite,
    EffectDirectionType,
    RegulatoryEffect,
)
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


def handle_uploaded_file(file):
    for line in file:
        cell_line, chrom, start, end, name, direction, effect_size = line.decode("utf-8").split(", ")

        # skip header
        if cell_line == "cell_line":
            continue

        dhs = DNaseIHypersensitiveSite(
            chromosome_name=chrom,
            location=NumericRange(int(start), int(end)),
            cell_line=cell_line,
        )
        dhs.save()

        effect_size = effect_size.strip()
        if effect_size == "":
            effect_size = None

        re = RegulatoryEffect(direction=EffectDirectionType(direction).value, effect_size=effect_size, sources=[dhs])
        re.save()
