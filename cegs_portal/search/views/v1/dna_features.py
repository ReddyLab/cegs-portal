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
            assembly
                * Should match a genome assembly that exists in the DB
            property (multiple)
                * "regeffects" - preload associated reg effects
            id_type
                * "accession"
                * "ensembl"
                * "name"
            feature_id
        """
        options = super().request_options(request)
        options["assembly"] = request.GET.get("assembly", None)
        options["feature_properties"] = request.GET.getlist("property", [])
        return options

    def get(self, request, options, data, id_type, feature_id):
        feature_reos = []
        for feature in data.all():
            sources = DNAFeatureSearch.source_reo_search(feature.accession_id)
            if sources.exists():
                sources = {"nav_prefix": f"source_for_{feature.accession_id}"}
            else:
                sources = None

            targets = DNAFeatureSearch.target_reo_search(feature.accession_id)
            if targets.exists():
                targets = {"nav_prefix": f"target_for_{feature.accession_id}"}
            else:
                targets = None

            feature_reos.append((feature, sources, targets))

        def sort_key(feature_reo):
            feature = feature_reo[0]
            return (feature.ref_genome, int(feature.ref_genome_patch or 0))

        feature_reos.sort(key=sort_key, reverse=True)

        if len(feature_reos) == 0:
            raise Http404(f"DNA Feature {id_type}/{feature_id} not found.")

        tabs = []
        first_feature = feature_reos[0][0]
        child_feature_type = None
        profile_header_feature_type = None
        # According to the documentation
        # (https://docs.djangoproject.com/en/4.2/ref/models/querysets/#django.db.models.query.QuerySet.exists),
        # calling .exists on something you are going to use anyway is unnecessary work. It results in two queries,
        # the `exists` query and the data loading query, instead of one data-loading query. So you can, instead,
        # wrap the property access that does the data loading in a `bool` to get basically the same result.
        if any(f[1] is not None or f[2] is not None for f in feature_reos):
            tabs.append("source target")

        if any(bool(f[0].closest_features.all()) for f in feature_reos):
            tabs.append("closest features")

        tabs.append("find nearby")

        if any(bool(f[0].children.all()) for f in feature_reos):
            tabs.append("children")

            first_child = first_feature.children.first()
            child_feature_type = first_child.get_feature_type_display()

        profile_header_feature_type = first_feature.get_feature_type_display()

        return super().get(
            request,
            options,
            {
                "features": data,
                "feature_name": "Genome Features",
                "feature_reos": feature_reos,
                "tabs": tabs,
                "child_feature_type": child_feature_type,
                "profile_header_feature_type": profile_header_feature_type
            },
        )

    def get_data(self, options, id_type, feature_id):
        return DNAFeatureSearch.id_search(
            id_type, feature_id, assembly=options["assembly"], feature_properties=options["feature_properties"]
        )


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
                * Should match a categorical facet value
            feature_type (multiple)
                * Should match a feature type (gene, transcript, etc.)
            format
                * "genoverse" - only relevant for json
            property (multiple)
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
        options["feature_properties"] = request.GET.getlist("property", [])
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
                options["feature_properties"],
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
