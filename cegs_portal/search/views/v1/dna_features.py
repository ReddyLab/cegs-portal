from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import Http404

from cegs_portal.search.json_templates.v1.dna_features import features
from cegs_portal.search.models import DNAFeature
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    TemplateJsonView,
)
from cegs_portal.utils.http_exceptions import Http400


class DNAFeatureId(ExperimentAccessMixin, TemplateJsonView):
    json_renderer = features
    template = "search/v1/dna_feature.html"

    def get_experiment_accession_id(self):
        try:
            return DNAFeatureSearch.expr_id(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_public(self):
        try:
            return DNAFeatureSearch.is_public(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_archived(self):
        try:
            return DNAFeatureSearch.is_archived(self.kwargs["feature_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            id_type
                * "accession"
                * "ensembl"
                * "name"
            feature_id
        """
        options = super().request_options(request)
        return options

    def get(self, request, options, data, id_type, feature_id):
        return super().get(request, options, {"features": data, "feature_name": "Genome Features"})

    def get_data(self, options, id_type, feature_id):
        return DNAFeatureSearch.id_search(id_type, feature_id)


class DNAFeatureLoc(TemplateJsonView):
    json_renderer = features
    template = "search/v1/dna_features.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * "application/json"
            assembly
                * Should match a genome assembly that exists in the DB
            facet (multiple)
                * Should match a discrete facet value
            feature_type (multiple)
                * Should match a feature type (gene, transcript, etc.)
            format
                * "genoverse" - only relevant for json
            region_properties
                * "regeffects" - preload associated reg effects
            search_type
                * "exact" - match location exactly
                * "overlap" - match any overlapping feature
            paginate - only used for JSON data, HTML is always paginated
            page - which page to show
                * int
        """
        options = super().request_options(request)
        options["assembly"] = request.GET.get("assembly", None)
        options["feature_types"] = request.GET.getlist("feature_type", [])
        options["region_properties"] = request.GET.getlist("property", [])
        options["search_type"] = request.GET.get("search_type", "overlap")
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["page"] = int(request.GET.get("page", 1))
        options["paginate"] = "page" in request.GET or bool(request.GET.get("paginate", False))

        return options

    def get(self, request, options, data, chromo, start, end):
        features_paginator = Paginator(data, 20)
        feature_page = features_paginator.get_page(options["page"])
        return super().get(
            request,
            options,
            {
                "features": feature_page,
                "feature_name": "Genome Features",
                "loc": {"chr": chromo, "start": int(start), "end": int(end)},
            },
        )

    def get_json(self, request, options, data, chromo, start, end):
        if options is not None and options.get("paginate", False):
            features_paginator = Paginator(data, 20)
            data = features_paginator.get_page(options["page"])

        return super().get_json(
            request,
            options,
            data,
        )

    def get_data(self, options, chromo, start, end) -> QuerySet[DNAFeature]:
        start = int(start)
        end = int(end)
        if chromo.isnumeric():
            chromo = f"chr{chromo}"
        try:
            loc_search_params = [
                chromo,
                start,
                end,
                options["assembly"],
                options["feature_types"],
                options["region_properties"],
                options["search_type"],
                options["facets"],
            ]
            if self.request.user.is_anonymous:
                features = DNAFeatureSearch.loc_search_public(*loc_search_params)
            elif self.request.user.is_superuser or self.request.user.is_portal_admin:
                features = DNAFeatureSearch.loc_search(*loc_search_params)
            else:
                features = DNAFeatureSearch.loc_search_with_private(
                    *loc_search_params, self.request.user.all_experiments()
                )
        except ValueError as e:
            raise Http400(e)

        return features
