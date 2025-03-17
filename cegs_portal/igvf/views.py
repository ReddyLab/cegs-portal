import json
import logging

from django.http import Http404, HttpResponseServerError, JsonResponse
from django.shortcuts import render
from django.views.generic import View

from cegs_portal.igvf.view_models import (
    CHROM_NAMES,
    LARGE_BUCKET_SIZE,
    SMALL_BUCKET_SIZE,
    CoverageType,
    Filter,
    FilterIntervals,
    GetIGVFException,
    default_facets,
    generate_data,
    get_experiment,
    get_filter,
    view_facets,
)
from cegs_portal.utils.http_exceptions import Http400

logger = logging.getLogger(__name__)


class CoverageView(View):
    def get(self, request, exp_id, *args, **kwargs):
        experiment = get_experiment(exp_id)
        if not experiment.exists():
            raise Http404(f"No IGVF experiment {exp_id} found")

        experiment = experiment.first()

        filter = Filter(
            chrom=None,
            categorical_facets=set(default_facets()),
            coverage_type=CoverageType.COUNT,
            numeric_intervals=FilterIntervals(
                effect=(float("-infinity"), float("infinity")), sig=(float("-infinity"), float("infinity"))
            ),
        )

        try:
            chrom_data, stats, source_urls = generate_data(exp_id, filter)
        except GetIGVFException as e:
            return HttpResponseServerError(e.args[0])

        return render(
            request,
            "coverage.html",
            {
                "accession_id": exp_id,
                "experiment": experiment,
                "source_urls": source_urls,
                "coverage": {
                    "chromosomes": chrom_data,
                    "default_facets": default_facets(),
                    "facets": view_facets(stats),
                    "reo_count": stats.reo_count,
                    "source_count": len(stats.sources),
                    "target_count": len(stats.genes),
                },
                "logged_in": not request.user.is_anonymous,
            },
        )

    def post(self, request, exp_id, *args, **kwargs):
        if not get_experiment(exp_id).exists():
            raise Http404(f"No IGVF experiment {exp_id} found")

        try:
            body = json.loads(request.body)
        except Exception as e:
            raise Http400(f"Invalid request body:\n{request.body}") from e

        if (zoom_chr := body.get("zoom")) is not None and zoom_chr not in CHROM_NAMES:
            raise Http400(f"Invalid chromosome in zoom: {zoom_chr}")
        coverage_type = body.get("coverage_type")

        try:
            body["filters"]
        except Exception as e:
            raise Http400(f'Invalid request body, no "filters" object:\n{request.body}') from e

        data_filter = get_filter(body["filters"], zoom_chr, coverage_type)
        try:
            chrom_data, stats, _ = generate_data(exp_id, data_filter)
        except GetIGVFException as e:
            return HttpResponseServerError(e.args[0])

        return JsonResponse(
            {
                "chromosomes": chrom_data,
                "bucket_size": SMALL_BUCKET_SIZE if data_filter.chrom is not None else LARGE_BUCKET_SIZE,
                "numeric_intervals": {
                    "effect": (stats.min_effect, stats.max_effect),
                    "sig": (stats.min_sig, stats.max_sig),
                },
                "reo_count": stats.reo_count,
                "source_count": len(stats.sources),
                "target_count": len(stats.genes),
            }
        )
