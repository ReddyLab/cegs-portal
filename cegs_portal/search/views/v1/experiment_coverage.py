import json
import pickle
from functools import lru_cache, reduce
from os.path import join

from django.contrib.staticfiles import finders

from cegs_portal.search.json_templates.v1.experiment_coverage import experiment_coverage
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.view_utils import JSON_MIME
from cegs_portal.utils.http_exceptions import Http500
from utils import flatten

INFINITY = float("Infinity")
NEG_INFINITY = float("-Infinity")


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


def filter_data(filters, data):
    new_data = shallow_clone(data)
    discrete_facets = set(filters[0])

    if len(discrete_facets) == 0:
        skip_disc_facets = True
    else:
        skip_disc_facets = False

    if len(filters) > 1:
        effect_size_interval, sig_interval = filters[1]
        skip_cont_facets = False
    else:
        effect_size_interval = [f["range"] for f in data["facets"] if f["name"] == "Effect Size"][0]
        sig_interval = [f["range"] for f in data["facets"] if f["name"] == "Significance"][0]
        skip_cont_facets = True

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

    min_effect = INFINITY
    max_effect = NEG_INFINITY

    min_sig = INFINITY
    max_sig = NEG_INFINITY

    for c, chromosome in enumerate(data["chromosomes"]):
        if len(sf_with_selections) > 0:
            for interval in chromosome["source_intervals"]:
                sources = interval["sources"]
                new_sources = 0
                new_target_buckets = set()
                for effects, target_buckets in sources:
                    new_regeffects = 0
                    for disc_facets, effect_size, sig in effects:
                        if skip_disc_facets or (
                            len([sf for sf in selected_sf if not sf.isdisjoint(disc_facets)]) == len_selected_sf
                        ):
                            min_effect, max_effect = min(min_effect, effect_size), max(max_effect, effect_size)
                            min_sig, max_sig = min(min_sig, sig), max(max_sig, sig)

                            if skip_cont_facets or (
                                effect_size >= effect_size_interval[0]
                                and effect_size <= effect_size_interval[1]
                                and sig >= sig_interval[0]
                                and sig <= sig_interval[1]
                            ):
                                new_regeffects += 1
                                new_target_buckets.update(target_buckets)

                    if new_regeffects > 0:
                        new_sources += 1

                if new_sources > 0:
                    new_data["chromosomes"][c]["source_intervals"].append(
                        {
                            "start": interval["start"],
                            "count": new_sources,
                            "assoc_targets": flatten(list(new_target_buckets)),
                        }
                    )
        else:
            new_data["chromosomes"][c]["source_intervals"] = [
                {
                    "start": interval["start"],
                    "count": len(interval["sources"]),
                    "assoc_targets": flatten(
                        list(reduce(lambda x, source: x | set(source[1]), interval["sources"], set()))
                    ),
                }
                for interval in chromosome["source_intervals"]
            ]

        if len(tf_with_selections) > 0:
            for interval in chromosome["target_intervals"]:
                targets = interval["targets"]
                new_targets = 0
                new_source_buckets = set()
                for effects, source_buckets in targets:
                    new_regeffects = 0
                    for disc_facets, effect_size, sig in effects:
                        if skip_disc_facets or (
                            len([tf for tf in selected_tf if not tf.isdisjoint(disc_facets)]) == len_selected_tf
                        ):
                            min_effect, max_effect = min(min_effect, effect_size), max(max_effect, effect_size)
                            min_sig, max_sig = min(min_sig, sig), max(max_sig, sig)

                            if skip_cont_facets or (
                                effect_size >= effect_size_interval[0]
                                and effect_size <= effect_size_interval[1]
                                and sig >= sig_interval[0]
                                and sig <= sig_interval[1]
                            ):
                                new_regeffects += 1
                                new_source_buckets.update(source_buckets)

                    if new_regeffects > 0:
                        new_targets += 1

                if new_targets > 0:
                    new_data["chromosomes"][c]["target_intervals"].append(
                        {
                            "start": interval["start"],
                            "count": new_targets,
                            "assoc_sources": flatten(list(new_source_buckets)),
                        }
                    )
        else:
            new_data["chromosomes"][c]["target_intervals"] = [
                {
                    "start": interval["start"],
                    "count": len(interval["targets"]),
                    "assoc_sources": flatten(
                        list(reduce(lambda x, target: x | set(target[1]), interval["targets"], set()))
                    ),
                }
                for interval in chromosome["target_intervals"]
            ]

    min_effect = effect_size_interval[0] if min_effect == INFINITY else min_effect
    max_effect = effect_size_interval[1] if max_effect == NEG_INFINITY else max_effect

    min_sig = sig_interval[0] if min_sig == INFINITY else min_sig
    max_sig = sig_interval[1] if max_sig == NEG_INFINITY else max_sig

    new_data["continuous_intervals"] = {
        "effect": (min_effect, max_effect),
        "sig": (min_sig, max_sig),
    }

    return new_data


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
        return filter_data(options["filters"], level1)
