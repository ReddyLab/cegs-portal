from functools import partial

from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from huey.contrib.djhuey import db_task

from cegs_portal.get_expr_data.models import ReoSourcesTargets, ReoSourcesTargetsSigOnly
from cegs_portal.uploads.data_generation import gen_all_coverage
from cegs_portal.uploads.data_loading.analysis import load as an_load
from cegs_portal.uploads.data_loading.experiment import load as expr_load
from cegs_portal.uploads.forms import UploadFileForm


@permission_required("search.add_experiment", raise_exception=True)
def upload(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            experiment_accession = request.POST["experiment_accession"]

            if (experiment_url := request.POST.get("experiment_url")) != "":
                handle_experiment_file(experiment_url, experiment_accession)
            elif (experiment_file := request.FILES.get("experiment_file")) is not None:
                handle_experiment_file(experiment_file, experiment_accession)

            if (analysis_url := request.POST.get("analysis_url")) != "":
                handle_analysis_file(analysis_url, experiment_accession)
            elif (analysis_file := request.FILES.get("analysis_file")) is not None:
                handle_analysis_file(analysis_file, experiment_accession)

            return HttpResponseRedirect(reverse("uploads:upload_complete"))
    else:
        form = UploadFileForm()
    return render(request, "uploads/upload.html", {"upload_form": form})


def upload_complete(request):
    return render(request, "uploads/upload_complete.html", {})


@db_task()
def handle_experiment_file(file, expr_accession):
    expr_load(file, expr_accession)


@db_task()
def handle_analysis_file(file, expr_accession):
    analysis_accession = an_load(file, expr_accession)
    ReoSourcesTargets.load_analysis(analysis_accession)
    ReoSourcesTargetsSigOnly.load_analysis(analysis_accession)
    transaction.on_commit(partial(gen_all_coverage, analysis_accession=analysis_accession))
