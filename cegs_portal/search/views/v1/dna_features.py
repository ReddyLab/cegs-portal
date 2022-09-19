from django.core.paginator import Paginator
from django.db.models import QuerySet

from cegs_portal.search.json_templates.v1.dna_features import features
from cegs_portal.search.models import DNAFeature
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, IdType
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.utils.http_exceptions import Http400


class DNAFeatureEnsembl(TemplateJsonView):
    json_renderer = features
    template = "search/v1/dna_feature.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
        """
        return super().request_options(request)

    def get(self, request, options, data, feature_id):
        return super().get(request, options, {"features": data, "feature_name": "Genome Features"})

    def get_data(self, _options, feature_id):
        return DNAFeatureSearch.id_search(IdType.ENSEMBL.value, feature_id)


class DNAFeatureId(TemplateJsonView):
    json_renderer = features
    template = "search/v1/dna_feature.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            id_type
                * "ensembl"
                * "name"
                * "havana"
                * "hgnc"
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
                * application/json
            format
                * genoverse, only relevant for json
            search_type
                * exact
                * overlap
            assembly
                * free-text, but should match a genome assembly that exists in the DB
        """
        options = super().request_options(request)
        options["assembly"] = request.GET.get("assembly", None)
        options["feature_types"] = request.GET.getlist("feature_type", [])
        options["region_properties"] = request.GET.getlist("property", [])
        options["search_type"] = request.GET.get("search_type", "overlap")
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["page"] = int(request.GET.get("page", 1))
        options["paginate"] = bool(request.GET.get("paginate", False))

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
            features = DNAFeatureSearch.loc_search(
                chromo,
                start,
                end,
                options["assembly"],
                options["feature_types"],
                options["region_properties"],
                options["search_type"],
                options["facets"],
            )
        except ValueError as e:
            raise Http400(e)

        return features
