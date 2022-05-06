from typing import cast

from django.core.paginator import Paginator

from cegs_portal.search.json_templates.v1.feature_exact import feature_exact
from cegs_portal.search.json_templates.v1.features import feature_assemblies
from cegs_portal.search.models.features import FeatureAssembly
from cegs_portal.search.view_models.v1 import FeatureSearch, IdType
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.utils.pagination_types import Pageable


class FeatureEnsembl(TemplateJsonView):
    json_renderer = feature_exact
    template = "search/v1/feature_exact.html"

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
        options["search_type"] = request.GET.get("search_type", "exact")
        return options

    def get(self, request, options, data, feature_id):
        return super().get(request, options, {"features": data})

    def get_data(self, options, feature_id):
        return FeatureSearch.id_search(IdType.ENSEMBL.value, feature_id, options["search_type"])


class Feature(TemplateJsonView):
    json_renderer = feature_assemblies
    template = "search/v1/features.html"

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
        options["feature_types"] = request.GET.get("feature_type", ["gene"])
        options["page"] = int(request.GET.get("page", 1))
        options["search_type"] = request.GET.get("search_type", "exact")
        return options

    def get(self, request, options, data, id_type, feature_id):
        return super().get(request, options, {"features": data, "feature_name": "Genome Features"})

    def get_data(self, options, id_type, feature_id):
        feature_results = FeatureSearch.id_search(id_type, feature_id, options["search_type"])
        features_paginator = Paginator(feature_results, 20)
        features_page = features_paginator.get_page(options["page"])
        return features_page


class FeatureLoc(TemplateJsonView):
    json_renderer = feature_assemblies
    template = "search/v1/features.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            format
                * genoverse
            search_type
                * exact
                * overlap
            assembly
                * free-text, but should match a genome assembly that exists in the DB
        """
        options = super().request_options(request)
        options["assembly"] = request.GET.get("assembly", None)
        options["feature_types"] = request.GET.getlist("feature_type", ["gene"])
        options["page"] = int(request.GET.get("page", 1))
        options["search_type"] = request.GET.get("search_type", "overlap")

        return options

    def get(self, request, options, data, chromo, start, end):
        return super().get(
            request,
            options,
            {"features": data, "feature_name": "Genome Features"},
            chromo,
            start,
            end,
        )

    def get_data(self, options, chromo, start, end) -> Pageable[FeatureAssembly]:
        if chromo.isnumeric():
            chromo = f"chr{chromo}"

        assemblies = FeatureSearch.loc_search(
            chromo, start, end, options["assembly"], options["feature_types"], options["search_type"]
        )
        assemblies_paginator = Paginator(assemblies, 20)
        assembly_page = assemblies_paginator.get_page(options["page"])

        return cast(Pageable[FeatureAssembly], assembly_page)
