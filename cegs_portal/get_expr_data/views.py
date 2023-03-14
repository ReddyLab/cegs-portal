import logging
import os
import re
from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.http import (
    FileResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic import View

from cegs_portal.get_expr_data.view_models import (
    EXPR_DATA_DIR,
    ReoDataSource,
    gen_output_filename,
    output_experiment_data_csv_task,
    output_experiment_data_list,
    validate_expr,
    validate_filename,
)
from cegs_portal.utils.http_exceptions import Http400

MAX_REGION_SIZE = 100_000

logger = logging.getLogger("django.request")

Loc = tuple[str, int, int]
LocList = list[Loc]


def maybe_bed(file):
    return file.content_type == "text/tab-separated-values" or file.name.endswith(".bed")


def try_process_bed(bed_file) -> LocList:
    loc_list = []
    for line in bed_file:
        #  Decoding with ASCII insted of utf-8 because the text we care about should
        #  always be valid ASCII, AFAIK. If it's not, we'll update this to utf-8.
        #
        #  Not using the csv module because it expects in iterable over strings and
        #  UploadedFile (the type of the bed_file parameter) is an iterable over
        #  byte strings.
        match = re.match(r"^(chr\w+)\t(\d+)\t(\d+)(\t.*)?$", line.decode("ascii"))
        if match is None:
            continue
        loc_list.append((match[1], int(match[2]), int(match[3])))

    return loc_list


def get_experiments(request) -> list[str]:
    experiments = request.GET.getlist("expr", [])
    if len(experiments) == 0:
        raise Http400("Invalid request; must specify at least one experiment by accession id")

    if not all(validate_expr(e) for e in experiments):
        raise Http400("Invalid request; invalid experiment id")

    return experiments


def get_region(request) -> Optional[Loc]:
    region = request.GET.get("region", None)

    if region is None:
        raise Http400(f"Region required {region}")

    match = re.match(r"^(chr\w+):(\d+)-(\d+)$", region)
    if match is None:
        raise Http400(f"Invalid region {region}")
    return (match[1], int(match[2]), int(match[3]))


def get_regions_file(request) -> LocList:
    try:
        file = request.FILES["regions"]
    except MultiValueDictKeyError as mvdke:
        raise Http400('Invalid request; file variable name should be "regions"') from mvdke

    if maybe_bed(file):
        regions = try_process_bed(file)
    else:
        raise Http400(f"Invalid regions file: unknown file type for {file.name}")

    return regions


def get_data_source(request) -> ReoDataSource:
    data_source = request.GET.get("datasource", "both")
    if data_source == "both":
        return ReoDataSource.BOTH
    if data_source == "sources":
        return ReoDataSource.SOURCES
    if data_source == "targets":
        return ReoDataSource.TARGETS
    raise Http400(f"Invalid data source: {data_source}")


class LocationExperimentDataView(LoginRequiredMixin, View):
    """
    Pull experiment data for a single region from the DB
    """

    def get(self, request, *args, **kwargs):
        try:
            experiments = get_experiments(request)
            region = get_region(request)
            data_source = get_data_source(request)
        except Http400 as error:
            return HttpResponseBadRequest(error)

        if region[1] >= region[2]:
            return HttpResponseBadRequest(
                "The lower value in the region must be smaller than the higher value: "
                f"{region[0]}:{region[1]}-{region[2]}."
            )

        if region[2] - region[1] > MAX_REGION_SIZE:
            return HttpResponseBadRequest(f"Please request a region smaller than {MAX_REGION_SIZE} base pairs.")

        data = output_experiment_data_list([region], experiments, data_source)
        return JsonResponse({"experiment data": data})


class RequestExperimentDataView(LoginRequiredMixin, View):
    """
    Kick off the task to pull experiment data from the DB
    for later download
    """

    def post(self, request, *args, **kwargs):
        try:
            experiments = get_experiments(request)
            regions = get_regions_file(request)
            data_source = get_data_source(request)
        except Http400 as error:
            return HttpResponseBadRequest(error)

        output_file = gen_output_filename(experiments)
        task = output_experiment_data_csv_task(regions, experiments, data_source, output_file)
        file_url = reverse("get_expr_data:experimentdata", args=[output_file])
        check_completion_url = reverse("tasks:status", args=[task.id])
        return JsonResponse(
            {
                "file location": file_url,
                "file progress": check_completion_url,
            }
        )


class ExperimentDataView(LoginRequiredMixin, View):
    def get(self, request, filename, *args, **kwargs):
        if validate_filename(filename):
            filename = os.path.join(EXPR_DATA_DIR, filename)
            if default_storage.exists(filename):
                return FileResponse(default_storage.open(filename, "rb"), as_attachment=True)

            return HttpResponseNotFound(
                f"File {filename} not found. Perhaps the file isn't finished being generated. Please try again later."
            )

        return HttpResponseBadRequest(f"Invalid filename: {filename}")
