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
from cegs_portal.utils import truthy_to_bool
from cegs_portal.utils.http_exceptions import Http400

DEFAULT_TABLE_LENGTH = 20
HG19 = "hg19"
HG38 = "hg38"
ALL_ASSEMBLIES = [HG38, HG19]  # Ordered by descending "importance"
VALID_FEATUREID_PROPS = {"regeffects"}
VALID_FEATURELOC_PROPS = {
    "regeffects",
    "screen_ccre",
    "effect_directions",
    "significant",
    "reo_source",
    "reporterassay",
    "crispri",
    "crispra",
    "parent_info",
}


def validate_properties(property_list):
    def f(properties):
        if not all(p in property_list for p in properties):
            raise Http400(f"Invalid query properties ({properties})")

    return f


validate_id_properties = validate_properties(VALID_FEATUREID_PROPS)
validate_loc_properties = validate_properties(VALID_FEATURELOC_PROPS)


def normalize_assembly(value):
    if value is None:
        return None

    match value.lower():
        case "grch38" | "hg38":
            return HG38
        case "grch37" | "hg19":
            return HG19
        case _:
            raise Http400(f"Invalid assembly {value}")


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
        options = super().request_options(request)
        options["assembly"] = normalize_assembly(request.GET.get("assembly", None))
        options["feature_properties"] = request.GET.getlist("property", [])
        validate_id_properties(options["feature_properties"])
        options["json_format"] = request.GET.get("format", None)
        options["sig_only"] = truthy_to_bool(request.GET.get("sig_only", True))
        return options

    def get(self, request, options, data, id_type, feature_id):
        feature_assemblies = []
        features = list(data.all())
        selected_feature = None
        genome_assembly_dict = {f.ref_genome: f for f in features}
        sorted_features = []
        assembly_list = []

        for genome_assembly in ALL_ASSEMBLIES:
            if (feature := genome_assembly_dict.get(genome_assembly)) is not None:
                sorted_features.append(feature)
                feature_assemblies.append(feature.ref_genome)

                # We want to mark one of the enabled genome assemblies as selected. If no assembly query
                # parameter has been passed in, we mark the first assembly that exists for this feature.
                # If there is an assembly query parameter we mark that genome assembly as selected.
                if (options["assembly"] is None and selected_feature is None) or (
                    options["assembly"] == genome_assembly
                ):
                    assembly_list.append((genome_assembly, "selected", genome_assembly))
                    selected_feature = feature
                else:
                    assembly_list.append((genome_assembly, "", genome_assembly))

            else:
                # This genome assembly doesn't exist for this feature, so we disable it in the dropdown.
                assembly_list.append((genome_assembly, "disabled", f"{genome_assembly} - Not Found"))

        if selected_feature is None:
            raise Http404(f"DNA Feature {id_type}/{feature_id} not found.")

        sources = DNAFeatureSearch.source_reo_search(selected_feature.accession_id)
        if sources.exists():
            sources = {"nav_prefix": f"source_for_{selected_feature.accession_id}"}
        else:
            sources = None

        targets = DNAFeatureSearch.target_reo_search(selected_feature.accession_id)
        if targets.exists():
            targets = {"nav_prefix": f"target_for_{selected_feature.accession_id}"}
        else:
            targets = None

        tabs = []
        child_feature_type = None

        reos = DNAFeatureSearch.non_targeting_reo_search(selected_feature.accession_id, options.get("sig_only"))
        if reos.exists() is not None:
            tabs.append("nearest reo")

        # According to the documentation
        # (https://docs.djangoproject.com/en/4.2/ref/models/querysets/#django.db.models.query.QuerySet.exists),
        # calling .exists on something you are going to use anyway is unnecessary work. It results in two queries,
        # the `exists` query and the data loading query, instead of one data-loading query. So you can, instead,
        # wrap the property access that does the data loading in a `bool` to get basically the same result.

        # Only Genes will have any "closest features" because "closest features" is the inverse relationship to "closest gene"
        closest_features = selected_feature.closest_features.all()
        if bool(closest_features):
            tabs.append("closest features")
            closest_features = list(closest_features)
            closest_features.sort(key=lambda f: abs(f.closest_gene_distance))

        tabs.append("find nearby")

        if bool(selected_feature.children.all()):
            tabs.append("children")

            first_child = selected_feature.children.first()
            child_feature_type = first_child.get_feature_type_display()

        return super().get(
            request,
            options,
            {
                "feature": selected_feature,
                "closest_features": closest_features,
                "sources": sources,
                "targets": targets,
                "reos": reos,
                "feature_name": selected_feature.name,
                "tabs": tabs,
                "child_feature_type": child_feature_type,
                "dna_feature_types": [feature_type.value for feature_type in DNAFeatureType],
                "closest_dna_feature_types": [
                    feature_type.value
                    for feature_type in DNAFeatureType
                    if feature_type not in [DNAFeatureType.GENE, DNAFeatureType.EXON, DNAFeatureType.TRANSCRIPT]
                ],
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


class DNAFeatureClosestFeatures(ExperimentAccessMixin, MultiResponseFormatView):
    json_renderer = features
    table_partial = "search/v1/partials/_closest_features.html"

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
            feature_type (multiple)
                * Should match a feature type (gene, transcript, etc.)
            id_type
                * "accession"
                * "ensembl"
                * "name"
            feature_id
        """
        options = super().request_options(request)
        options["assembly"] = normalize_assembly(request.GET.get("assembly", None))
        options["feature_types"] = request.GET.getlist("type", [])
        return options

    def get(self, request, options, data, id_type, feature_id):
        if request.headers.get("HX-Request"):
            return render(
                request,
                self.table_partial,
                {
                    "closest_features": data,
                },
            )

        raise Http400("Access this only using htmx or JSON")

    def get_data(self, options, id_type, feature_id):
        if self.request.user.is_anonymous:
            features = DNAFeatureSearch.id_closest_search_public(id_type, feature_id, options["feature_types"])
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            features = DNAFeatureSearch.id_closest_search(id_type, feature_id, options["feature_types"])
        else:
            features = DNAFeatureSearch.id_closest_search_private(
                id_type, feature_id, options["feature_types"], self.request.user.all_experiments()
            )
        return features


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
                Be careful combining these, their effects are no necessarily orthogonal
                * "regeffects" - preload associated reg effects
                * "screen_ccre" - include screen cCRE type
                * "effect_directions" - include effect directions of associated REOs
                * "significant" - include only feature that are the source of significant REOs
                * "reo_source" - include features that are the source for an REO
                * "reporterassay", "crispri", "crispra" - include features from these kinds of experiments
            search_type
                * "exact" - match location exactly
                * "overlap" - match any overlapping feature
            paginate - only used for JSON data, HTML is always paginated
            page - which page to show
                * int
            per_page - Number of features per page
                * int
        """
        options = super().request_options(request)
        options["assembly"] = normalize_assembly(request.GET.get("assembly", HG38))
        options["feature_types"] = request.GET.getlist("feature_type", [])
        options["feature_properties"] = request.GET.getlist("property", [])
        validate_loc_properties(options["feature_properties"])
        options["search_type"] = request.GET.get("search_type", "overlap")
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        options["paginate"] = truthy_to_bool(request.GET.get("paginate", False))
        options["json_format"] = request.GET.get("format", None)
        options["dist"] = int(request.GET.get("dist", 0))
        options["tsv_format"] = request.GET.get("tsv_format", None)

        return options

    def get(self, request, options, data, chromo, start, end):
        features_paginator = Paginator(data, options["per_page"])
        feature_page = features_paginator.get_page(options["page"])
        assembly_list = []
        selected = False

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
                },
            )

        for ref_genome in ALL_ASSEMBLIES:
            if (options["assembly"] is None and not selected) or (options["assembly"] == ref_genome):
                assembly_list.append((ref_genome, "selected", ref_genome))
                selected = True
            else:
                assembly_list.append((ref_genome, "", ref_genome))

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
