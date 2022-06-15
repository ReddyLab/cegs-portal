import json
import pickle
from functools import lru_cache
from os.path import join

from django.contrib.staticfiles import finders

from cegs_portal.search.json_templates.v1.experiment_coverage import experiment_coverage
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.view_utils import JSON_MIME
from cegs_portal.utils.http_exceptions import Http500


def flatten(list_):
    result = []
    for item in list_:
        if isinstance(item, list) or isinstance(item, tuple):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def filter_data(_filters, data):
    return data


def display_transform(data):
    result = {"chromosomes": []}
    for chromosome in data["chromosomes"]:
        chrom_data = {
            "chrom": chromosome["chrom"],
            "bucket_size": chromosome["bucket_size"],
            "target_intervals": [],
            "source_intervals": [],
        }

        for interval in chromosome["target_intervals"]:
            new_interval = {"start": interval["start"], "count": len(interval["targets"])}
            sources = set()
            for target in interval["targets"]:
                assoc_sources = target[1]
                for i in range(0, len(assoc_sources), 2):
                    sources.add((assoc_sources[i], assoc_sources[i + 1]))

            new_interval["assoc_sources"] = flatten(list(sources))
            chrom_data["target_intervals"].append(new_interval)

        for interval in chromosome["source_intervals"]:
            new_interval = {"start": interval["start"], "count": len(interval["sources"])}
            targets = set()
            for source in interval["sources"]:
                assoc_targets = source[1]
                for i in range(0, len(assoc_targets), 2):
                    targets.add((assoc_targets[i], assoc_targets[i + 1]))
            new_interval["assoc_targets"] = flatten(list(targets))
            chrom_data["source_intervals"].append(new_interval)

        result["chromosomes"].append(chrom_data)
    return result


@lru_cache(maxsize=100)
def load_coverage(exp_acc_id):
    level1_filename = finders.find(join("search", "experiments", exp_acc_id, "level1.pkl"))
    with open(level1_filename, "rb") as level1_file:
        level1 = pickle.load(level1_file)
    return level1


class ExperimentCoverageView(TemplateJsonView):
    json_renderer = experiment_coverage

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            search_type
                * exact
                * like
                * start
                * in
        """
        options = super().request_options(request)
        try:
            body = json.loads(request.body)
        except Exception as e:
            raise Http500(f"Invalid request body:\n{request.body}\n\nError:\n{e}")

        try:
            options["filters"] = body["filters"]
        except Exception as e:
            raise Http500(f'Invalid request body, no "filters" object:\n{request.body}\n\nError:\n{e}')

        return options

    def post(self, request, options, data, exp_acc_id):
        raise Http500(
            (
                f'This is a JSON-only API. Please request using "Accept: {JSON_MIME}" header or '
                f'pass "{JSON_MIME}" as the "accept" GET parameter.'
            )
        )

    def post_data(self, options, exp_acc_id):
        validate_accession_id(exp_acc_id)
        level1 = load_coverage(exp_acc_id)
        filters = options["filters"]

        return display_transform(filter_data(filters, level1))
