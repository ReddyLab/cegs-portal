import json
from functools import lru_cache
from os.path import join

import exp_viz
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from exp_viz import Filter, FilterIntervals

from cegs_portal.search.json_templates.v1.experiment_coverage import experiment_coverage
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.view_utils import JSON_MIME
from cegs_portal.utils.http_exceptions import Http500


@lru_cache(maxsize=100)
def load_coverage(exp_acc_id):
    level1_filename = finders.find(join("search", "experiments", exp_acc_id, "level1.bin"))
    return exp_viz.load_coverage_data(level1_filename)


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

    def post_json(self, _request, options, data, *args, **kwargs):
        return HttpResponse(data.to_json(), content_type=JSON_MIME)

    def post_data(self, options, exp_acc_id):
        validate_accession_id(exp_acc_id)
        new_level1 = load_coverage(exp_acc_id)

        filters = options["filters"]

        data_filter = Filter()
        data_filter.discrete_facets = set(filters[0])

        if len(filters) > 1:
            effect_size_interval, sig_interval = filters[1]
            data_filter_intervals = FilterIntervals()
            data_filter_intervals.effect = (effect_size_interval[0], effect_size_interval[1])
            data_filter_intervals.sig = (sig_interval[0], sig_interval[1])
            data_filter.continuous_intervals = data_filter_intervals

        filtered_data = exp_viz.filter_coverage_data(data_filter, new_level1)
        return filtered_data
