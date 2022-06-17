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


def shallow_clone(data):
    return {
        "chromosomes": [
            {
                "chrom": chrom["chrom"],
                "bucket_size": chrom["bucket_size"],
                "target_intervals": list(),
                "source_intervals": list(),
            }
            for chrom in data["chromosomes"]
        ]
    }


def flatten(list_):
    result = []
    for item in list_:
        if isinstance(item, list) or isinstance(item, tuple):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def filter_data(filters, data):
    new_data = shallow_clone(data)
    discrete_facets = set(filters[0])
    effect_size_interval = filters[1][0]
    sig_interval = filters[1][1]

    source_facets = [
        set(f["values"].keys())
        for f in data["facets"]
        if f["type"] == "FacetType.DISCRETE" and "source" in f["coverage"]
    ]
    target_facets = [
        set(f["values"].keys())
        for f in data["facets"]
        if f["type"] == "FacetType.DISCRETE" and "target" in f["coverage"]
    ]

    sf_with_selections = [f for f in source_facets if not discrete_facets.isdisjoint(f)]
    tf_with_selections = [f for f in target_facets if not discrete_facets.isdisjoint(f)]

    selected_sf = [f & discrete_facets for f in sf_with_selections]
    len_selected_sf = len(selected_sf)
    selected_tf = [f & discrete_facets for f in tf_with_selections]
    len_selected_tf = len(selected_tf)

    min_effect = float("Infinity")
    max_effect = float("-Infinity")

    min_sig = float("Infinity")
    max_sig = float("-Infinity")

    for c, chromosome in enumerate(data["chromosomes"]):
        if len(sf_with_selections) > 0:
            for i, interval in enumerate(chromosome["source_intervals"]):
                sources = interval["sources"]
                new_sources = []
                for effects, target_buckets in sources:
                    new_regeffects = []
                    for disc_facets, effect_size, sig in effects:
                        if len([sf for sf in selected_sf if not sf.isdisjoint(disc_facets)]) == len_selected_sf:
                            min_effect, max_effect = min(min_effect, effect_size), max(max_effect, effect_size)
                            min_sig, max_sig = min(min_sig, sig), max(max_sig, sig)

                            if (
                                effect_size >= effect_size_interval[0]
                                and effect_size <= effect_size_interval[1]
                                and sig >= sig_interval[0]
                                and sig <= sig_interval[1]
                            ):
                                new_regeffects.append((disc_facets, effect_size, sig))

                    if len(new_regeffects) > 0:
                        new_sources.append((new_regeffects, target_buckets))

                if len(new_sources) > 0:
                    new_data["chromosomes"][c]["source_intervals"].append(
                        {"start": interval["start"], "sources": new_sources}
                    )
        else:
            new_data["chromosomes"][c]["source_intervals"] = chromosome["source_intervals"]

        if len(tf_with_selections) > 0:
            for i, interval in enumerate(chromosome["target_intervals"]):
                targets = interval["targets"]
                new_targets = []
                for effects, source_buckets in targets:
                    new_regeffects = []
                    for disc_facets, effect_size, sig in effects:
                        if len([tf for tf in selected_tf if not tf.isdisjoint(disc_facets)]) == len_selected_tf:
                            min_effect, max_effect = min(min_effect, effect_size), max(max_effect, effect_size)
                            min_sig, max_sig = min(min_sig, sig), max(max_sig, sig)

                            if (
                                effect_size >= effect_size_interval[0]
                                and effect_size <= effect_size_interval[1]
                                and sig >= sig_interval[0]
                                and sig <= sig_interval[1]
                            ):
                                new_regeffects.append((disc_facets, effect_size, sig))

                    if len(new_regeffects) > 0:
                        new_targets.append((new_regeffects, source_buckets))

                if len(new_targets) > 0:
                    new_data["chromosomes"][c]["target_intervals"].append(
                        {"start": interval["start"], "targets": new_targets}
                    )
        else:
            new_data["chromosomes"][c]["target_intervals"] = chromosome["target_intervals"]

    min_effect = effect_size_interval[0] if min_effect == float("Infinity") else min_effect
    max_effect = effect_size_interval[1] if max_effect == float("-Infinity") else max_effect

    min_sig = sig_interval[0] if min_sig == float("Infinity") else min_sig
    max_sig = sig_interval[1] if max_sig == float("-Infinity") else max_sig

    return new_data, (min_effect, max_effect), (min_sig, max_sig)


def display_transform(data):
    result = {"chromosomes": []}
    min_source_count = float("Infinity")
    max_source_count = 0
    min_target_count = float("Infinity")
    max_target_count = 0
    for chromosome in data["chromosomes"]:
        chrom_data = {
            "chrom": chromosome["chrom"],
            "bucket_size": chromosome["bucket_size"],
            "source_intervals": [],
            "target_intervals": [],
        }

        for interval in chromosome["source_intervals"]:
            source_count = len(interval["sources"])
            min_source_count = min(min_source_count, source_count)
            max_source_count = max(max_source_count, source_count)
            new_interval = {"start": interval["start"], "count": source_count}

            targets = set()
            for source in interval["sources"]:
                targets.update(source[1])

            new_interval["assoc_targets"] = flatten(list(targets))
            chrom_data["source_intervals"].append(new_interval)

        for interval in chromosome["target_intervals"]:
            target_count = len(interval["targets"])
            min_target_count = min(min_target_count, target_count)
            max_target_count = max(max_target_count, target_count)
            new_interval = {"start": interval["start"], "count": target_count}

            sources = set()
            for target in interval["targets"]:
                sources.update(target[1])

            new_interval["assoc_sources"] = flatten(list(sources))
            chrom_data["target_intervals"].append(new_interval)

        result["chromosomes"].append(chrom_data)
        result["count_intervals"] = {
            "source": (min_source_count, max_source_count),
            "target": (min_target_count, max_target_count),
        }
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
        new_data, effect_interval, sig_interval = filter_data(filters, level1)
        display_data = display_transform(new_data)
        display_data["continuous_intervals"] = {
            "effect": effect_interval,
            "sig": sig_interval,
        }
        return display_data
