from functools import partial

from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from huey.contrib.djhuey import db_task

from cegs_portal.get_expr_data.models import ReoSourcesTargets, ReoSourcesTargetsSigOnly
from cegs_portal.task_status.decorators import handle_error
from cegs_portal.task_status.models import TaskStatus
from cegs_portal.uploads.data_generation import gen_all_coverage
from cegs_portal.uploads.data_loading.analysis import load as an_load
from cegs_portal.uploads.data_loading.experiment import load as expr_load
from cegs_portal.uploads.forms import UploadFileForm
from cegs_portal.uploads.view_models import add_experiment_to_user

BAD_URLS = ["", None]


@permission_required("search.add_experiment", raise_exception=True)
def upload(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            experiment_accession = request.POST["experiment_accession"]
            experiment_data = None
            analysis_data = None

            if (experiment_url := request.POST.get("experiment_url")) not in BAD_URLS:
                experiment_data = experiment_url
            elif (experiment_file := request.FILES.get("experiment_file")) is not None:
                experiment_data = experiment_file

            if (analysis_url := request.POST.get("analysis_url")) not in BAD_URLS:
                analysis_data = analysis_url
            elif (analysis_file := request.FILES.get("analysis_file")) is not None:
                analysis_data = analysis_file

            handle_upload(experiment_data, analysis_data, experiment_accession, request.user)
            return HttpResponseRedirect(reverse("uploads:upload_complete"))
    else:
        form = UploadFileForm()
    return render(request, "uploads/upload.html", {"upload_form": form})


def upload_complete(request):
    return render(request, "uploads/upload_complete.html", {})


@db_task()
def handle_upload(experiment_file, analysis_file, experiment_accession, user):
    match experiment_file, analysis_file:
        case (None, None):
            desc = "Null Upload"
        case (_, None):
            desc = "Experiment Upload"
        case (None, _):
            desc = "Analysis Upload"
        case (_, _):
            desc = "Experiment and Analysis Upload"

    status = TaskStatus(user=user, description=f"({experiment_accession}) {desc}")
    status.start()

    if experiment_file is not None:
        expr_load(experiment_file, experiment_accession)
        transaction.on_commit(
            handle_error(partial(add_experiment_to_user, experiment_accession=experiment_accession, user=user), status)
        )

    if analysis_file is not None:
        analysis_accession = an_load(analysis_file, experiment_accession)
        ReoSourcesTargets.load_analysis(analysis_accession)
        ReoSourcesTargetsSigOnly.load_analysis(analysis_accession)
        transaction.on_commit(handle_error(partial(gen_all_coverage, analysis_accession=analysis_accession), status))

    transaction.on_commit(lambda: status.finish())
