from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import render

from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.json_templates.v1.dna_features import features
from cegs_portal.search.models import DNAFeature, DNAFeatureType
from cegs_portal.search.tsv_templates.v1.dna_features import dnafeatures as f_tsv
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import DNAFeatureSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    MultiResponseFormatView,
)
from cegs_portal.utils.http_exceptions import Http400

DEFAULT_TABLE_LENGTH = 20
GRCH37 = "GRCh37"
GRCH38 = "GRCh38"


class DNAFeatureId(ExperimentAccessMixin, MultiResponseFormatView):
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

        def get_sig_only(value):
            if value == "0" or value == "false" or value == "False":
                return False
            else:
                return True

        options = super().request_options(request)
        options["assembly"] = request.GET.get("assembly", None)
        options["feature_properties"] = request.GET.getlist("property", [])
        options["json_format"] = request.GET.get("format", None)
        sig_only = request.GET.get("sig_only", True)
        options["sig_only"] = get_sig_only(sig_only)
        return options

    def get(self, request, options, data, id_type, feature_id):
        feature_reos = []
        reo_page = None
        all_assemblies = [GRCH38, GRCH37]  # Ordered by "importance"
        feature_assemblies = []

        features = list(data.all())
        ref_genome_dict = {f.ref_genome: f for f in features}
        sorted_features = []
        for ref_genome in all_assemblies:
            if (feature := ref_genome_dict.get(ref_genome)) is not None:
                sorted_features.append(feature)
                feature_assemblies.append(feature.ref_genome)

        for feature in sorted_features:
            if options["assembly"] is not None and feature.ref_genome != options["assembly"]:
                continue

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

            reos = DNAFeatureSearch.non_targeting_reo_search(feature.accession_id, options.get("sig_only"))
            if reos.exists():
                paginated_reos = Paginator(reos, DEFAULT_TABLE_LENGTH)
                reo_page = paginated_reos.page(1)
            else:
                reo_page = None

            feature_reos.append((feature, sources, targets, reo_page))

        if len(feature_reos) == 0:
            raise Http404(f"DNA Feature {id_type}/{feature_id} not found.")

        tabs = []
        first_feature = feature_reos[0][0]
        child_feature_type = None
        # According to the documentation
        # (https://docs.djangoproject.com/en/4.2/ref/models/querysets/#django.db.models.query.QuerySet.exists),
        # calling .exists on something you are going to use anyway is unnecessary work. It results in two queries,
        # the `exists` query and the data loading query, instead of one data-loading query. So you can, instead,
        # wrap the property access that does the data loading in a `bool` to get basically the same result.
        if any(f[3] is not None for f in feature_reos):
            tabs.append("nearest reo")

        if any(bool(f[0].closest_features.all()) for f in feature_reos):
            tabs.append("closest features")

        tabs.append("find nearby")

        if any(bool(f[0].children.all()) for f in feature_reos):
            tabs.append("children")

            first_child = first_feature.children.first()
            child_feature_type = first_child.get_feature_type_display()

        assembly_list = []
        for assembly in all_assemblies:
            if assembly in feature_assemblies:
                assembly_list.append((assembly, "", assembly))
            else:
                assembly_list.append((assembly, "disabled", f"{assembly} - Not Found"))

        return super().get(
            request,
            options,
            {
                "features": [first_feature],
                "feature_name": "Genome Features",
                "feature_reos": feature_reos[:1],
                "tabs": tabs,
                "child_feature_type": child_feature_type,
                "dna_feature_types": [feature_type.value for feature_type in DNAFeatureType],
                "all_assemblies": assembly_list,
                "id_type": id_type,
                "feature_id": feature_id,
            },
        )

    def get_json(self, request, options, data, id_type, feature_id):
        if options["assembly"] is None:
            return super().get_json(request, options, data, id_type, feature_id)

        features = [feature for feature in data.all() if feature.ref_genome == options["assembly"]]
        return super().get_json(request, options, features, id_type, feature_id)

    def get_data(self, options, id_type, feature_id):
        return DNAFeatureSearch.id_search(id_type, feature_id, None, feature_properties=options["feature_properties"])


class DNAFeatureLoc(MultiResponseFormatView):
    json_renderer = features
    template = "search/v1/dna_features.html"
    table_partial = "search/v1/partials/_features.html"
    tsv_renderer = f_tsv

    def request_options(self, request):
        """
        GET queries used:
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
        options["assembly"] = request.GET.get("assembly", GRCH38)
        options["feature_types"] = request.GET.getlist("feature_type", [])
        options["feature_properties"] = request.GET.getlist("property", [])
        options["search_type"] = request.GET.get("search_type", "overlap")
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        options["json_format"] = request.GET.get("format", None)
        options["dist"] = int(request.GET.get("dist", 0))
        options["tsv_format"] = request.GET.get("tsv_format", None)
        return options

    def get(self, request, options, data, chromo, start, end):
        features_paginator = Paginator(data, options["per_page"])
        feature_page = features_paginator.get_page(options["page"])
        assembly_list = []
        selected = False
        all_assemblies = [GRCH38, GRCH37]

        for ref_genome in all_assemblies:
            if (options["assembly"] is None and not selected) or (options["assembly"] == ref_genome):
                assembly_list.append((ref_genome, "selected", ref_genome))
                selected = True
            else:
                assembly_list.append((ref_genome, "", ref_genome))

        if request.headers.get("HX-Request"):
            return render(
                request,
                self.table_partial,
                {
                    "features": feature_page,
                    "loc": {"chr": chromo, "start": int(start), "end": int(end)},
                    "dist": options["dist"],
                    "feature_types": options["feature_types"],
                    "assembly": options["assembly"],
                    "dna_feature_types": [feature_type.value for feature_type in DNAFeatureType],
                    "all_assemblies": all_assemblies,
                },
            )

        return super().get(
            request,
            options,
            {
                "features": feature_page,
                "feature_name": "Genome Features",
                "loc": {"chr": chromo, "start": int(start), "end": int(end)},
                "dist": options["dist"],
                "feature_types": options["feature_types"],
                "assembly": options["assembly"],
                "dna_feature_types": [feature_type.value for feature_type in DNAFeatureType],
                "all_assemblies": assembly_list,
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

    def get_tsv(self, request, options, data, chromo, start, end):
        if is_bed6(options):
            filename = f"dna_features_{chromo}_{start}_{end}.bed"
        else:
            filename = f"dna_features_{chromo}_{start}_{end}.tsv"
        return super().get_tsv(request, options, data, filename=filename)

    def get_data(self, options, chromo, start, end) -> QuerySet[DNAFeature]:
        start = int(start)
        end = int(end)
        search_start = max(start - options["dist"], 0)
        search_end = end + options["dist"]

        if chromo.isnumeric():
            chromo = f"chr{chromo}"
        try:
            loc_search_params = [
                chromo,
                search_start,
                search_end,
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
