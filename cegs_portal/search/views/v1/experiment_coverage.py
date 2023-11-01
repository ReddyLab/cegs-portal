import json
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from functools import lru_cache
from os.path import join

from django.contrib.staticfiles import finders
from django.http import HttpResponse
from exp_viz import (
    Filter,
    FilterIntervals,
    filter_coverage_data_allow_threads,
    load_coverage_data_allow_threads,
    merge_filtered_data,
)

from cegs_portal.search.json_templates.v1.combined_experiments import (
    combined_experiments,
)
from cegs_portal.search.json_templates.v1.experiment_coverage import experiment_coverage
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.search.view_models.v1 import ExperimentCoverageSearch
from cegs_portal.search.views.custom_views import MultiResponseFormatView
from cegs_portal.search.views.view_utils import JSON_MIME
from cegs_portal.utils.http_exceptions import Http400

CHROM_NAMES = {
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "X",
    "Y",
    "MT",
}


@lru_cache(maxsize=100)
def load_coverage(exp_acc_id, analysis_acc_id, chrom):
    if chrom is None:
        filename = finders.find(join("search", "experiments", exp_acc_id, analysis_acc_id, "level1.ecd"))
    else:
        filename = finders.find(join("search", "experiments", exp_acc_id, analysis_acc_id, f"level2_{chrom}.ecd"))

    return load_coverage_data_allow_threads(filename)


def get_analysis(exp_acc_id: str) -> tuple[str, str]:
    ids = exp_acc_id.split("/")
    if len(ids) == 1:
        validate_accession_id(ids[0])
        return ExperimentCoverageSearch.default_analysis(ids[0])
    elif len(ids) == 2:
        validate_accession_id(ids[0])
        validate_accession_id(ids[1])
        return (ids[0], ids[1])
    else:
        raise Http400(f"Invalid experiment id {exp_acc_id}")


def get_analyses(exp_acc_ids: list[str]) -> list[tuple[str, str]]:
    exp_analysis_pairs = []
    exps_only = []
    for exp_id in exp_acc_ids:
        ids = exp_id.split("/")
        if len(ids) == 1:
            validate_accession_id(ids[0])
            exps_only.append(ids[0])
        elif len(ids) == 2:
            validate_accession_id(ids[0])
            validate_accession_id(ids[1])
            exp_analysis_pairs.append((ids[0], ids[1]))
        else:
            raise Http400(f"Invalid experiment id {exp_id}")

    exp_analysis_pairs.extend(ExperimentCoverageSearch.default_analyses(exps_only))
    return exp_analysis_pairs


def get_filter(filters):
    data_filter = Filter()
    data_filter.categorical_facets = set(filters[0])

    if len(filters) > 1:
        effect_size_interval, sig_interval = filters[1]
        data_filter_intervals = FilterIntervals()
        data_filter_intervals.effect = (effect_size_interval[0], effect_size_interval[1])
        data_filter_intervals.sig = (sig_interval[0], sig_interval[1])
        data_filter.numeric_intervals = data_filter_intervals

    return data_filter


class ExperimentCoverageView(MultiResponseFormatView):
    json_renderer = experiment_coverage

    def request_options(self, request):
        """
        GET queries used:
            exp (multiple)
                * Experiment Accession ID
        POST body:
            filters:
                * object - the filter values
            chromosomes:
                * array - names of chromosomes that will be merged
            zoom:
                * str - the chromosome that's zoomed in on
        """
        options = super().request_options(request)
        options["exp_acc_id"] = request.GET.get("exp", None)

        if options["exp_acc_id"] is None:
            raise Http400("Must query an experiment")

        try:
            body = json.loads(request.body)
        except Exception as e:
            raise Http400(f"Invalid request body:\n{request.body}") from e

        try:
            options["filters"] = body["filters"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "filters" object:\n{request.body}') from e

        try:
            options["chromosomes"] = body["chromosomes"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "chromosomes" object:\n{request.body}') from e

        if (zoom_chr := body.get("zoom", None)) is not None and zoom_chr not in CHROM_NAMES:
            raise Http400(f"Invalid chromosome in zoom: {zoom_chr}")
        options["zoom_chr"] = zoom_chr

        return options

    def post(self, request, options, data):
        raise Http400(
            (
                f'This is a JSON-only API. Please request using "Accept: {JSON_MIME}" header or '
                f'pass "{JSON_MIME}" as the "accept" GET parameter.'
            )
        )

    def post_json(self, _request, options, data, *args, **kwargs):
        return HttpResponse(data.to_json(), content_type=JSON_MIME)

    def post_data(self, options):
        accession_ids = get_analysis(options["exp_acc_id"])
        data_filter = get_filter(options["filters"])
        loaded_data = load_coverage(*accession_ids, options["zoom_chr"])
        filtered_data = filter_coverage_data_allow_threads(data_filter, loaded_data)

        return filtered_data


class CombinedExperimentView(MultiResponseFormatView):
    json_renderer = combined_experiments

    def request_options(self, request):
        """
        GET queries used:
            exp (multiple)
                * Experiment Accession ID
        POST body:
            filters:
                * object - the filter values
            chromosomes:
                * array - names of chromosomes that will be merged
            zoom:
                * str - the chromosome that's zoomed in on
        """
        options = super().request_options(request)
        options["exp_acc_ids"] = request.GET.getlist("exp", [])

        if len(options["exp_acc_ids"]) == 0:
            raise Http400("Must query at least 1 experiment")

        try:
            body = json.loads(request.body)
        except Exception as e:
            raise Http400(f"Invalid request body:\n{request.body}") from e

        try:
            options["filters"] = body["filters"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "filters" object:\n{request.body}') from e

        try:
            options["chromosomes"] = body["chromosomes"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "chromosomes" object:\n{request.body}') from e

        if (zoom_chr := body.get("zoom", None)) is not None and zoom_chr not in CHROM_NAMES:
            raise Http400(f"Invalid chromosome in zoom: {zoom_chr}")
        options["zoom_chr"] = zoom_chr

        return options

    def post(self, request, options, data):
        raise Http400(
            (
                f'This is a JSON-only API. Please request using "Accept: {JSON_MIME}" header or '
                f'pass "{JSON_MIME}" as the "accept" GET parameter.'
            )
        )

    def post_json(self, _request, options, data, *args, **kwargs):
        return HttpResponse(data.to_json(), content_type=JSON_MIME)

    def post_data(self, options):
        accession_ids = get_analyses(options["exp_acc_ids"])

        data_filter = get_filter(options["filters"])

        with ThreadPoolExecutor() as executor:
            load_to_acc_id = {
                executor.submit(load_coverage, exp_acc_id, analysis_acc_id, options["zoom_chr"]): (
                    exp_acc_id,
                    analysis_acc_id,
                )
                for exp_acc_id, analysis_acc_id in accession_ids
            }
            loaded_data = wait(load_to_acc_id, return_when=ALL_COMPLETED)
            filter_to_acc_id = {
                executor.submit(filter_coverage_data_allow_threads, data_filter, load_future.result())
                for load_future in loaded_data.done
            }
            filtered_data = wait(filter_to_acc_id, return_when=ALL_COMPLETED)

        return merge_filtered_data([d.result() for d in filtered_data.done], options["chromosomes"])
