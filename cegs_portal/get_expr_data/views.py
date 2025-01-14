import json
import logging
import re
from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest
from django.http import FileResponse, Http404, JsonResponse
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic import View

from cegs_portal.get_expr_data.view_models import (
    DataState,
    Facets,
    ReoDataSource,
    analyses_for_facets,
    experiments_for_facets,
    file_exists,
    file_status,
    for_facet_query_input,
    gen_output_filename,
    open_file,
    output_experiment_data_csv_task,
    output_experiment_data_list,
    validate_an,
    validate_expr,
    validate_filename,
)
from cegs_portal.utils.http_exceptions import Http400

MAX_REGION_SIZE = 100_000_000
HG19 = "hg19"
HG38 = "hg38"

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


def get_experiments_analyses(request) -> tuple[Optional[list[str]], Optional[list[str]]]:
    # We want to use "None" as a sentinial value to indicate that a user wants to
    # search across all experiments or analyses. Unforunately getlist will return an
    # empty list if None is the default, so we have to set a different default and
    # then change to None.
    experiments = request.GET.getlist("expr", 0)
    analyses = request.GET.getlist("an", 0)

    experiments = None if experiments == 0 else experiments
    analyses = None if analyses == 0 else analyses

    if experiments is not None and not all(validate_expr(e) for e in experiments):
        raise Http400("Invalid request; invalid experiment id")

    if analyses is not None and not all(validate_an(a) for a in analyses):
        raise Http400("Invalid request; invalid analysis id")

    return experiments, analyses


def get_region(request) -> Optional[Loc]:
    region = request.GET.get("region", None)

    if region is None:
        return None

    match = re.match(r"^(chr\w+):(\d+)-(\d+)$", region)
    if match is None:
        raise Http400(f"Invalid region {region}")

    region = (match[1], int(match[2]), int(match[3]))

    if region[1] >= region[2]:
        raise BadRequest(
            "The lower value in the region must be smaller than the higher value: "
            f"{region[0]}:{region[1]}-{region[2]}."
        )

    if region[2] - region[1] > MAX_REGION_SIZE:
        raise BadRequest(f"Please request a region smaller than {MAX_REGION_SIZE} base pairs.")

    return region


def get_assembly(request) -> Optional[str]:
    assembly = request.GET.get("assembly", None)

    if assembly is None:
        return None

    match assembly.lower():
        case "hg19" | "grch37":
            return HG19
        case "hg38" | "grch38":
            return HG38

    raise BadRequest(f"Invalid assembly {assembly}. Please specify one of hg19, grch38, hg38, or grch38.")


def get_regions_file(request) -> Optional[LocList]:
    try:
        file = request.FILES["regions"]
    except MultiValueDictKeyError:
        return None

    if maybe_bed(file):
        regions = try_process_bed(file)
    else:
        raise Http400(f"Invalid regions file: unknown file type for {file.name}")

    return regions


def get_data_source(request) -> ReoDataSource:
    match request.GET.get("datasource", "both"):
        case "both":
            return ReoDataSource.BOTH
        case "sources":
            return ReoDataSource.SOURCES
        case "targets":
            return ReoDataSource.TARGETS
        case "everything":
            return ReoDataSource.EVERYTHING
        case invalid_data_source:
            raise Http400(f"Invalid data source: {invalid_data_source}")


def get_facets(request) -> Facets:
    facets = Facets()
    try:
        facets_json = request.POST["facets"]
    except MultiValueDictKeyError:
        return facets

    try:
        facet_array = json.loads(facets_json)
    except json.JSONDecodeError:
        return facets

    facets.categorical_facets = facet_array[0]
    if len(facet_array) == 2:
        facets.effect_size_range = (facet_array[1][0][0], facet_array[1][0][1])
        facets.sig_range = (facet_array[1][1][0], facet_array[1][1][1])

    return facets


def get_query_facets(request) -> list[int]:
    try:
        str_facets = request.GET.getlist("f", [])
        int_facets = [int(f) for f in str_facets]
    except ValueError as e:
        raise BadRequest(f"Invalid facet values: {str_facets}") from e

    return int_facets


def parse_source_locs_json(source_locs: str) -> list[tuple[str, int, int, str]]:
    locs = []
    while match := re.search(r'\((chr\w+),\\"\[(\d+),(\d+)\)\\",(\w+)\)', source_locs):
        chrom = match[1]
        start = int(match[2])
        end = int(match[3])
        accession_id = match[4]
        locs.append((chrom, start, end, accession_id))
        source_locs = source_locs[match.end() :]

    return locs


def parse_target_info_json(target_info: Optional[str]) -> list[tuple[str, str]]:
    if target_info is None:
        return []

    info = []
    while match := re.search(r'\(chr\w+,\\"\[\d+,\d+\)\\",([\w-]+),(\w+)\)', target_info):
        gene_symbol = match[1]
        ensembl_id = match[2]
        info.append((gene_symbol, ensembl_id))
        target_info = target_info[match.end() :]
    return info


def parse_source_target_data_json(reo_data):
    return reo_data | {
        "source_locs": parse_source_locs_json(reo_data["source_locs"]),
        "target_info": parse_target_info_json(reo_data["target_info"]),
    }


class LocationExperimentDataView(LoginRequiredMixin, View):
    """
    Pull experiment data for a single region from the DB
    """

    def get(self, request, *args, **kwargs):
        try:
            experiments, analyses = get_experiments_analyses(request)
            region = get_region(request)
            data_source = get_data_source(request)
            assembly = get_assembly(request)
            facets = get_query_facets(request)
            if region is not None and data_source == ReoDataSource.EVERYTHING:
                raise Http400("Specifying regions and asking for everything are mutually exclusive")

            if region is None and data_source != ReoDataSource.EVERYTHING:
                raise Http400("Must specify regions if not asking for everything")

        except Http400 as error:
            raise BadRequest() from error

        if request.user.is_anonymous:
            user_experiments = []
        else:
            user_experiments = request.user.all_experiments()

        if len(facets) > 0:
            facets = for_facet_query_input(facets)
            facet_experiments = experiments_for_facets(facets)
            user_experiments = [expr for expr in user_experiments if expr in facet_experiments]

            if experiments is not None:
                # The interesction of experiments and facet_experiments
                experiments = [expr for expr in experiments if expr in facet_experiments]
            else:
                experiments = facet_experiments

            facet_analyses = analyses_for_facets(facets)
            if analyses is not None:
                # The interesction of analyses and facet_analyses
                analyses = [a for a in analyses if a in facet_analyses]
            else:
                analyses = facet_analyses

        data = output_experiment_data_list(user_experiments, [region], experiments, analyses, data_source, assembly)
        return JsonResponse({"experiment data": data})


class RequestExperimentDataView(LoginRequiredMixin, View):
    """
    Kick off the task to pull experiment data from the DB
    for later download
    """

    def post(self, request, *args, **kwargs):
        try:
            experiments, analyses = get_experiments_analyses(request)
            if experiments is None and analyses is None:
                raise Http400("Invalid request; must specify at least one experiment or analysis by accession id")

            regions = get_regions_file(request)
            data_source = get_data_source(request)
            facets = get_facets(request)
        except Http400 as error:
            raise BadRequest() from error

        output_file = gen_output_filename(experiments, analyses)
        output_experiment_data_csv_task(request.user, regions, experiments, analyses, data_source, facets, output_file)
        file_url = reverse("get_expr_data:experimentdata", args=[output_file])
        check_completion_url = reverse("get_expr_data:dataprogress", args=[output_file])
        return JsonResponse(
            {
                "file location": file_url,
                "file progress": check_completion_url,
            }
        )


class ExperimentDataView(LoginRequiredMixin, View):
    def get(self, request, filename, *args, **kwargs):
        if not validate_filename(filename):
            raise BadRequest(f"Invalid filename: {filename}")

        if not file_exists(filename):
            raise Http404(
                f"File {filename} not found. Perhaps the file isn't finished being generated. Please try again later."
            )

        return FileResponse(open_file(filename), as_attachment=True)


class ExperimentDataProgressView(LoginRequiredMixin, View):
    def get(self, request, filename, *args, **kwargs):
        if not validate_filename(filename):
            raise BadRequest(f"Invalid filename: {filename}")

        match file_status(filename, request.user):
            case DataState.NOT_FOUND:
                raise Http404(f"Unable to determine progress on file {filename}")
            case other_state:
                return JsonResponse({"file progress": other_state})
