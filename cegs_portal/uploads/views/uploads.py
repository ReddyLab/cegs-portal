import logging
from functools import partial

from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from huey.contrib.djhuey import db_task

from cegs_portal.get_expr_data.models import ReoSourcesTargets, ReoSourcesTargetsSigOnly
from cegs_portal.search.views.view_utils import JSON_MIME
from cegs_portal.task_status.decorators import handle_error
from cegs_portal.task_status.models import TaskStatus
from cegs_portal.uploads.data_generation import gen_all_coverage
from cegs_portal.uploads.data_loading.analysis import load as an_load
from cegs_portal.uploads.data_loading.compressed import load as c_load
from cegs_portal.uploads.data_loading.experiment import load as expr_load
from cegs_portal.uploads.forms import UploadFileForm
from cegs_portal.uploads.validators import validate_experiment_accession_id
from cegs_portal.uploads.view_models import (
    add_experiment_to_user,
    get_next_experiment_accession,
)

BAD_URLS = ["", None]

logger = logging.getLogger(__name__)


def get_data_value(request, value):
    if (data_url := request.POST.get(f"{value}_url")) not in BAD_URLS:
        return data_url
    elif (data_file := request.FILES.get(f"{value}_file")) is not None:
        return data_file


@permission_required("search.add_experiment", raise_exception=True)
def upload(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            json_response = request.headers.get("accept") == JSON_MIME or request.POST.get("accept") == JSON_MIME

            experiment_accession = request.POST.get("experiment_accession")

            if experiment_accession in ["", None]:
                experiment_accession = get_next_experiment_accession()

            validate_experiment_accession_id(experiment_accession)

            full_data = get_data_value(request, "full")

            if full_data is not None:
                task_status = TaskStatus(
                    user=request.user,
                    description=f"({experiment_accession}) Compressed Full Experiment Information Upload",
                )
                handle_full_upload(full_data, experiment_accession, task_status, request.user)
            else:
                experiment_data = get_data_value(request, "experiment")
                analysis_data = get_data_value(request, "analysis")

                match experiment_data, analysis_data:
                    case (None, None):
                        desc = "Null Upload"
                    case (_, None):
                        desc = "Experiment Upload"
                    case (None, _):
                        desc = "Analysis Upload"
                    case (_, _):
                        desc = "Experiment and Analysis Upload"

                task_status = TaskStatus(user=request.user, description=f"({experiment_accession}) {desc}")
                handle_partial_upload(experiment_data, analysis_data, experiment_accession, task_status, request.user)

            logger.info(f"Upload handled: {task_status.status}")

            if json_response:
                return JsonResponse({"task_status_id": task_status.id})
            else:
                return render(request, "uploads/upload_complete.html", {"task_status": task_status})
    else:
        form = UploadFileForm()
    return render(request, "uploads/upload.html", {"upload_form": form})


@db_task()
def handle_full_upload(full_file, experiment_accession, task_status, user):
    """Handle upload as single compressed file"""
    task_status.start()

    logger.info(f"{experiment_accession}: Starting upload")

    c_load_error = handle_error(c_load, task_status)
    analysis_accession = c_load_error(full_file, experiment_accession)

    transaction.on_commit(
        handle_error(partial(add_experiment_to_user, experiment_accession=experiment_accession, user=user), task_status)
    )

    logger.info(f"{experiment_accession}: Adding data to ReoSourcesTargets")
    ReoSourcesTargets.load_analysis(analysis_accession)
    ReoSourcesTargetsSigOnly.load_analysis(analysis_accession)

    logger.info(f"{experiment_accession}: Generating coverage/graph files")
    transaction.on_commit(handle_error(partial(gen_all_coverage, analysis_accession=analysis_accession), task_status))
    logger.info(f"{experiment_accession}: Done")
    transaction.on_commit(lambda: task_status.finish())


@db_task()
def handle_partial_upload(experiment_file, analysis_file, experiment_accession, task_status, user):
    """Handle upload as two parts: experiment_file, if applicable, then analysis_file if applicable"""

    task_status.start()

    logger.info(f"{experiment_accession}: Starting partial upload")

    if experiment_file is not None:
        expr_load_error = handle_error(expr_load, task_status)
        expr_load_error(experiment_file, experiment_accession)

        transaction.on_commit(
            handle_error(
                partial(add_experiment_to_user, experiment_accession=experiment_accession, user=user), task_status
            )
        )

    if analysis_file is not None:
        an_load_error = handle_error(an_load, task_status)
        analysis_accession = an_load_error(analysis_file, experiment_accession)

        ReoSourcesTargets.load_analysis(analysis_accession)
        ReoSourcesTargetsSigOnly.load_analysis(analysis_accession)
        transaction.on_commit(
            handle_error(partial(gen_all_coverage, analysis_accession=analysis_accession), task_status)
        )

    logger.info(f"{experiment_accession}: Done")
    transaction.on_commit(lambda: task_status.finish())
