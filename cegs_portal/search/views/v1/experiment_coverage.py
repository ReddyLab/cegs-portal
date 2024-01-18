import json
import logging
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from functools import lru_cache
from os.path import join

from django.contrib.staticfiles import finders
from django.http import HttpResponse
from exp_viz import (
    Filter,
    FilterIntervals,
    SetOpFeature,
    filter_coverage_data_allow_threads,
    load_coverage_data_allow_threads,
    load_feature_data_allow_threads,
    merge_filtered_data,
)

from cegs_portal.search.json_templates.v1.combined_experiments import (
    combined_experiments,
)
from cegs_portal.search.json_templates.v1.experiment_coverage import experiment_coverage
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.search.views.custom_views import MultiResponseFormatView
from cegs_portal.search.views.view_utils import JSON_MIME
from cegs_portal.utils.http_exceptions import Http400

CHROM_NAMES = [
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
]

SET_OPS = ["i", "u"]

logger = logging.getLogger("django.request")


@lru_cache(maxsize=100)
def load_coverage(acc_id, chrom):
    exp_acc_id, analysis_acc_id = acc_id.split("/")
    if chrom is None:
        filename = finders.find(join("search", "experiments", exp_acc_id, analysis_acc_id, "level1.ecd"))
    else:
        filename = finders.find(join("search", "experiments", exp_acc_id, analysis_acc_id, f"level2_{chrom}.ecd"))
    logger.debug(f"coverage file: {filename}")
    return load_coverage_data_allow_threads(filename)


def load_features(acc_id, chrom):
    exp_acc_id, analysis_acc_id = acc_id.split("/")
    if chrom is None:
        filename = finders.find(join("search", "experiments", exp_acc_id, analysis_acc_id, "level1.fd"))
    else:
        filename = finders.find(join("search", "experiments", exp_acc_id, analysis_acc_id, f"level2_{chrom}.fd"))

    return acc_id, load_feature_data_allow_threads(filename)


def calc_set(combinations, features):
    stack = []
    try:
        for item in combinations:
            if item == "i":
                x, y = stack[-2:]
                x.intersection(y)  # mutates x
                stack.pop()  # drops y
            elif item == "u":
                x, y = stack[-2:]
                x.union(y)  # mutates x
                stack.pop()  # drops y
            else:
                stack.append(features[item])
    except IndexError:
        raise Http400(f"Invalid set operations: [{', '.join(combinations)}]")

    if len(stack) != 1:
        raise Http400(f"Invalid set operations: [{', '.join(combinations)}]")
    return stack[0]


def get_analyses(combinations):
    return [analysis for analysis in combinations if analysis not in SET_OPS]


def validate_accession_string(accession_string):
    if isinstance(accession_string, str):
        ids = accession_string.split("/")
        return len(ids) == 2 and all(validate_accession_id(a) is None for a in ids)

    return False


def validate_combinations(combinations):
    experiment_count = 0
    for item in combinations:
        if item in SET_OPS:
            pass
        elif validate_accession_string(item):
            experiment_count += 1
        else:
            raise Http400(f"Invalid value {item}")

    return experiment_count


def get_filter(filters, chrom, combination_features=None):
    data_filter = Filter()
    data_filter.categorical_facets = set(filters[0])
    if chrom is not None:
        data_filter.chrom = CHROM_NAMES.index(chrom)

    if len(filters) > 1:
        effect_size_interval, sig_interval = filters[1]
        data_filter_intervals = FilterIntervals()
        data_filter_intervals.effect = (effect_size_interval[0], effect_size_interval[1])
        data_filter_intervals.sig = (sig_interval[0], sig_interval[1])
        data_filter.numeric_intervals = data_filter_intervals

    match combination_features:
        case "sources":
            data_filter.set_op_feature = SetOpFeature.Source
        case "targets":
            data_filter.set_op_feature = SetOpFeature.Target
        case "sources-targets":
            data_filter.set_op_feature = SetOpFeature.SourceTarget
        case _:
            data_filter.set_op_feature = None

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
        if not validate_accession_string(options["exp_acc_id"]):
            raise Http400(f"Invalid experiment id {options['exp_acc_id']}")

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
        logger.debug("response json")
        logger.debug(data.to_json())
        return HttpResponse(data.to_json(), content_type=JSON_MIME)

    def post_data(self, options):
        logger.debug("Creating Filter")
        data_filter = get_filter(options["filters"], options["zoom_chr"])
        logger.debug("Loading Coverage File")
        loaded_data = load_coverage(options["exp_acc_id"], options["zoom_chr"])
        logger.debug("Filtering Coverage")
        filtered_data = filter_coverage_data_allow_threads(data_filter, loaded_data, None)
        logger.debug("Returning Filtered data")
        return filtered_data


class CombinedExperimentView(MultiResponseFormatView):
    json_renderer = combined_experiments

    def request_options(self, request):
        """
        POST body:
            filters:
                * object - the filter values
            chromosomes:
                * array - names of chromosomes that will be merged
            zoom:
                * str - the chromosome that's zoomed in on
            combinations:
                * object describing how to combine the experiments
        """
        options = super().request_options(request)

        try:
            body = json.loads(request.body)
        except Exception as e:
            raise Http400(f"Invalid request body:\n{request.body}") from e

        combinations = body["combinations"]
        if validate_combinations(combinations) == 0:
            raise Http400("Must query at least 1 experiment")
        options["combinations"] = combinations

        try:
            options["filters"] = body["filters"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "filters" object:\n{request.body}') from e

        try:
            options["chromosomes"] = body["chromosomes"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "chromosomes" object:\n{request.body}') from e

        options["combination_features"] = body.get("combination_features")

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
        accession_ids = get_analyses(options["combinations"])

        data_filter = get_filter(options["filters"], options["zoom_chr"], options["combination_features"])

        with ThreadPoolExecutor() as executor:
            load_to_acc_id = {
                executor.submit(load_coverage, acc_id, options["zoom_chr"]): (acc_id,) for acc_id in accession_ids
            }
            loaded_data = wait(load_to_acc_id, return_when=ALL_COMPLETED)

            load_feat_to_acc_id = {
                executor.submit(load_features, acc_id, options["zoom_chr"]): (acc_id,) for acc_id in accession_ids
            }
            loaded_features = wait(load_feat_to_acc_id, return_when=ALL_COMPLETED)
            loaded_features = dict(load_future.result() for load_future in loaded_features.done)
            included_features = calc_set(options["combinations"], loaded_features)

            filter_to_acc_id = {
                executor.submit(
                    filter_coverage_data_allow_threads, data_filter, load_future.result(), included_features
                )
                for load_future in loaded_data.done
            }
            filtered_data = wait(filter_to_acc_id, return_when=ALL_COMPLETED)

        return merge_filtered_data([d.result() for d in filtered_data.done], options["chromosomes"])
