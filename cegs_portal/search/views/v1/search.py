import re
from enum import Enum, auto
from typing import Optional
from urllib.parse import unquote_plus

from django.core.exceptions import BadRequest
from django.core.paginator import Paginator
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View

from cegs_portal.search.forms import SearchForm
from cegs_portal.search.helpers.options import is_bed6
from cegs_portal.search.json_templates.v1.feature_counts import (
    feature_counts as fc_json,
)
from cegs_portal.search.json_templates.v1.search_results import (
    search_results as sr_json,
)
from cegs_portal.search.models import ChromosomeLocation, DNAFeatureType
from cegs_portal.search.models.utils import IdType
from cegs_portal.search.tsv_templates.v1.search_results import sig_reos as sr
from cegs_portal.search.view_models.v1 import Search
from cegs_portal.search.view_models.v1.search import EXPERIMENT_SOURCES_TEXT
from cegs_portal.search.views.custom_views import MultiResponseFormatView
from cegs_portal.search.views.v1.search_types import FeatureCountResult, Loc
from cegs_portal.users.models import UserType
from cegs_portal.utils.http_exceptions import Http303, Http400

CHROMO_RE = re.compile(r"((chr1\d|chr2[0-2]|chr[\dxym])\s*:\s*(\d[\d,]*)(\s*-\s*(\d[\d,]*))?)(\s+|$)", re.IGNORECASE)
ACCESSION_RE = re.compile(r"(DCP[a-z]{1,4}[0-9a-f]{8,10})(\s+|$)", re.IGNORECASE)
ENSEMBL_RE = re.compile(r"(ENS[0-9a-z]+)(\s+|$)", re.IGNORECASE)
ASSEMBLY_RE = re.compile(r"(hg19|hg38|grch37|grch38)(\s+|$)", re.IGNORECASE)
POSSIBLE_GENE_NAME_RE = re.compile(r"([A-Z0-9][A-Z0-9\.\-]+)(\s+|$)", re.IGNORECASE)

HG19 = "hg19"
HG38 = "hg38"

MAX_REGION_SIZE = 100_000_000


class ParseWarning(Enum):
    TOO_MANY_LOCS = auto()
    IGNORE_LOC = auto()
    IGNORE_TERMS = auto()


class SearchType(Enum):
    LOCATION = auto()
    ID = auto()


def parse_query(
    query: str,
) -> tuple[
    Optional[SearchType], list[tuple[IdType, str]], Optional[ChromosomeLocation], Optional[str], set[ParseWarning]
]:
    terms: list[tuple[IdType, str]] = []
    location: Optional[ChromosomeLocation] = None
    assembly: str = HG38
    warnings: set[ParseWarning] = set()
    search_type = None

    query = query.strip()

    # Avoid an infinite loop by making sure `query` gets shorter
    # every iteration and stopping if it doesn't
    old_query_len = len(query) + 1
    while query != "" and old_query_len != len(query):
        old_query_len = len(query)
        if match := re.match(CHROMO_RE, query):
            if search_type == SearchType.ID:
                warnings.add(ParseWarning.IGNORE_LOC)
            elif search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.TOO_MANY_LOCS)
            else:
                search_type = SearchType.LOCATION
                chromo = match.group(2)
                start = match.group(3).replace(",", "")
                end = match.group(5).replace(",", "") if match.group(5) is not None else None
                location = ChromosomeLocation(chromo, start, end)

            query = query[match.end() :]
            continue

        if match := re.match(ENSEMBL_RE, query):
            if search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.IGNORE_TERMS)
            else:
                terms.append(IdType.ENSEMBL.associate(match.group(1)))
                search_type = SearchType.ID

            query = query[match.end() :]
            continue

        if match := re.match(ACCESSION_RE, query):
            if search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.IGNORE_TERMS)
            else:
                terms.append(IdType.ACCESSION.associate(match.group(1)))
                search_type = SearchType.ID

            query = query[match.end() :]
            continue

        if match := re.match(ASSEMBLY_RE, query):
            token = match.group(1).lower()

            # Normalize token
            if token in ("hg19", "grch37"):
                assembly = HG19
            elif token in ("hg38", "grch38"):
                assembly = HG38

            query = query[match.end() :]
            continue

        if match := re.match(POSSIBLE_GENE_NAME_RE, query):
            if search_type == SearchType.LOCATION:
                warnings.add(ParseWarning.IGNORE_TERMS)
            else:
                terms.append(IdType.GENE_NAME.associate(match.group(1)))
                search_type = SearchType.ID

            query = query[match.end() :]
            continue

    return search_type, terms, location, assembly, warnings


def parse_source_locs_html(
    source_locs: list[tuple[Optional[str], Optional[str], Optional[str]]]
) -> list[tuple[str, str]]:
    locs = []
    for source_loc in source_locs:
        if source_loc[0] is None:
            continue

        chrom, loc, accession_id = source_loc
        if match := re.match(r"\[(\d+),(\d+)\)", loc):
            start = int(match[1])
            end = int(match[2])
            locs.append((f"{chrom}:{start:,}-{end:,}", accession_id))

    return locs


def parse_target_info_html(
    target_infos: list[tuple[Optional[str], Optional[str], Optional[str], Optional[str]]]
) -> list[tuple[str, str]]:
    info = []
    for target_info in target_infos:
        if target_info[2] is None:
            continue

        _, _, gene_symbol, ensembl_id = target_info
        info.append((gene_symbol, ensembl_id))
    return info


def parse_source_target_data_html(reo_data):
    return reo_data | {
        "source_locs": parse_source_locs_html(reo_data["source_locs"]),
        "target_info": parse_target_info_html(reo_data["target_info"]),
    }


def feature_redirect(feature):
    id_type, feature_id = feature
    url = reverse("search:dna_features", args=[id_type, feature_id])
    raise Http303("Specific feature Id", location=url)


class SearchView(MultiResponseFormatView):
    json_renderer = sr_json
    template = "search/v1/search_results.html"

    def request_options(self, request):
        options = super().request_options(request)
        options["search_query"] = request.GET.get("query", "")
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["selected-tab"] = request.GET.get("tab", None)
        return options

    def get(self, request, options, data, *args, **kwargs):
        data["form"] = SearchForm()
        data["sig_reg_effects"] = [
            [parse_source_target_data_html(reo_data) for reo_data in reo_group]
            for _, reo_group in data["sig_reg_effects"]
        ]
        data["logged_in"] = not request.user.is_anonymous
        return super().get(request, options, data, *args, **kwargs)

    def get_data(self, options):
        unquoted_search_query = unquote_plus(options["search_query"])
        search_type, query_terms, location, assembly_name, warnings = parse_query(unquoted_search_query)

        sig_reos = []
        features = []
        if search_type == SearchType.LOCATION:
            assert location is not None

            if location.range.lower >= location.range.upper:
                raise Http400(
                    f"Invalid location; lower bound ({location.range.lower}) "
                    f"larger than upper bound ({location.range.upper})"
                )

            if self.request.user.is_anonymous:
                features = Search.dnafeature_loc_search_public(location, assembly_name, options["facets"])
                sig_reos = Search.sig_reo_loc_search(
                    location, assembly_name, options["facets"], user_type=UserType.ANONYMOUS
                )
                feature_counts = Search.feature_counts(location, assembly_name, options["facets"])
            elif self.request.user.is_superuser or self.request.user.is_portal_admin:
                features = Search.dnafeature_loc_search(location, assembly_name, options["facets"])
                sig_reos = Search.sig_reo_loc_search(
                    location,
                    assembly_name,
                    options["facets"],
                    user_type=UserType.ADMIN,
                )
                feature_counts = Search.feature_counts(
                    location, assembly_name, options["facets"], user_type=UserType.ADMIN
                )
            else:
                features = Search.dnafeature_loc_search_with_private(
                    location, assembly_name, options["facets"], self.request.user.all_experiments()
                )
                sig_reos = Search.sig_reo_loc_search(
                    location,
                    assembly_name,
                    options["facets"],
                    user_type=UserType.LOGGED_IN,
                    private_experiments=self.request.user.all_experiments(),
                )
                feature_counts = Search.feature_counts(
                    location, assembly_name, options["facets"], UserType.LOGGED_IN, self.request.user.all_experiments()
                )

        elif search_type == SearchType.ID:
            if len(query_terms) == 1:
                feature_redirect(query_terms[0])

            if self.request.user.is_anonymous:
                features = Search.dnafeature_ids_search_public(query_terms, assembly_name)
            elif self.request.user.is_superuser or self.request.user.is_portal_admin:
                features = Search.dnafeature_ids_search(query_terms, assembly_name)
            else:
                features = Search.dnafeature_ids_search_with_private(
                    query_terms, assembly_name, self.request.user.all_experiments()
                )

            if features.count() == 1:
                feature = features[0]
                width = feature.location.upper - feature.location.lower
                browser_padding = width // 10
                location = ChromosomeLocation(
                    # Increase the location "width" to ensure white space on either side of the feature in
                    # in the genome browser
                    feature.chrom_name,
                    str(max(0, feature.location.lower - browser_padding)),
                    str(feature.location.upper + browser_padding),
                )
                assembly_name = feature.ref_genome

            feature_counts = None
        else:
            raise Http400(f"Invalid Query: {options['search_query']}")

        facets = Search.experiment_facet_search()

        match options["selected-tab"]:
            case "tab-summary":
                tab_summary_selected, tab_effects_selected, tab_features_selected = True, False, False
            case "tab-effects":
                tab_summary_selected, tab_effects_selected, tab_features_selected = False, True, False
            case "tab-features":
                tab_summary_selected, tab_effects_selected, tab_features_selected = False, False, True
            case _:
                tab_summary_selected, tab_effects_selected, tab_features_selected = True, False, False

        return {
            "location": location,
            "region": location,
            "assembly": assembly_name,
            "features": features,
            "sig_reg_effects": sig_reos,
            "facets": facets,
            "search_type": search_type.name,
            "query": options["search_query"],
            "facets_query": options["facets"],
            "warnings": {w.name for w in warnings},
            "feature_counts": feature_counts,
            "sig_reo_count_source": EXPERIMENT_SOURCES_TEXT,
            "sig_reo_count_gene": DNAFeatureType.GENE.value,
            "dna_feature_types": [feature_type.value for feature_type in DNAFeatureType],
            "tab_effects_selected": tab_effects_selected,
            "tab_summary_selected": tab_summary_selected,
            "tab_features_selected": tab_features_selected,
        }


def get_region(request) -> Optional[Loc]:
    region = request.GET.get("region", None)

    if region is None:
        return None

    match = re.match(r"^(chr\w+):(\d+)-(\d+)$", region)
    if match is None:
        raise Http400(f"Invalid region {region}")

    region = (match[1], int(match[2]), int(match[3]))

    if region[1] >= region[2]:
        raise BadRequest(
            "The lower value in the region must be smaller than the higher value: "
            f"{region[0]}:{region[1]}-{region[2]}."
        )

    if region[2] - region[1] > MAX_REGION_SIZE:
        raise BadRequest(f"Please request a region smaller than {MAX_REGION_SIZE} base pairs.")

    return ChromosomeLocation(region[0], region[1], region[2])


def get_assembly(request) -> Optional[str]:
    assembly = request.GET.get("assembly", None)

    if assembly is None:
        return HG38

    match assembly.lower():
        case "hg19" | "grch37":
            return HG19
        case "hg38" | "grch38":
            return HG38

    raise BadRequest(f"Invalid assembly {assembly}. Please specify one of hg19, grch38, hg38, or grch38.")


class FeatureCountView(MultiResponseFormatView):
    json_renderer = fc_json
    template = "search/v1/partials/_search_feature_counts.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            region
                * a genomic location, in the form of "chrN:start-end"
            assembly
                * the reference genome to search against. Defaults to hg38
        """
        options = super().request_options(request)
        options["region"] = get_region(request)
        options["assembly"] = get_assembly(request)
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]

        return options

    def get_data(self, options) -> FeatureCountResult:
        if self.request.user.is_anonymous:
            feature_counts = Search.feature_counts(options["region"], options["assembly"], options["facets"])
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            feature_counts = Search.feature_counts(
                options["region"], options["assembly"], options["facets"], UserType.ADMIN
            )
        else:
            feature_counts = Search.feature_counts(
                options["region"],
                options["assembly"],
                options["facets"],
                UserType.LOGGED_IN,
                self.request.user.all_experiments(),
            )

        return {
            "region": options["region"],
            "assembly": options["assembly"],
            "feature_counts": feature_counts,
            "facets": options["facets"],
            "sig_reo_count_source": EXPERIMENT_SOURCES_TEXT,
            "sig_reo_count_gene": DNAFeatureType.GENE.value,
        }


class SignificantExperimentDataView(View):
    """
    Pull experiment data for a single region from the DB
    """

    def get(self, request, *args, **kwargs):
        assembly = get_assembly(request)
        facets = [int(facet) for facet in request.GET.getlist("facet", [])]

        try:
            region = get_region(request)
            if region is None:
                raise Http400("Must specify a region")
        except Http400 as error:
            raise BadRequest() from error

        if self.request.user.is_anonymous:
            results = Search.sig_reo_loc_search(region, assembly, facets, user_type=UserType.ANONYMOUS)
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            results = Search.sig_reo_loc_search(
                region,
                assembly,
                facets,
                user_type=UserType.ADMIN,
            )
        else:
            results = Search.sig_reo_loc_search(
                region,
                assembly,
                facets,
                user_type=UserType.LOGGED_IN,
                private_experiments=self.request.user.all_experiments(),
            )

        return render(
            request,
            "search/v1/partials/_sig_reg_effects.html",
            {
                "sig_reg_effects": [
                    [parse_source_target_data_html(reo_data) for reo_data in reo_group] for _, reo_group in results
                ]
            },
        )


class FeatureSignificantREOsView(MultiResponseFormatView):
    """
    Show significant REOs associated with one or more DNA Feature types in a given area.
    """

    template = "search/v1/partials/_feature_sig_reg_effects_modal.html"
    tsv_renderer = sr

    def request_options(self, request):
        """
        GET queries used:
            assembly
                * Should match a genome assembly that exists in the DB
            facet (multiple)
                * Should match a categorical facet value
            feature_type (multiple)
                * Should match a feature type (gene, transcript, etc.)
            region
                * genome location in chrom:lower-upper format
            tsv_format (optional)
                * bed6
        """

        options = super().request_options(request)
        options["assembly"] = get_assembly(request)
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        options["features"] = request.GET.getlist("feature_type", [])
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["tsv_format"] = request.GET.get("tsv_format", None)
        try:
            region = get_region(request)
            if region is None:
                raise Http400("Must specify a region")
            options["region"] = region
        except Http400 as error:
            raise BadRequest() from error
        return options

    def get(self, request, options, data):
        sig_reos_paginator = Paginator(data, options["per_page"])
        sig_reos_page = sig_reos_paginator.get_page(options["page"])

        features = "".join(f"&feature_type={feature}" for feature in options["features"])
        facets = "".join(f"&facet={facet}" for facet in options["facets"])
        content_query = f"region={request.GET['region']}&assembly={options['assembly']}{features}{facets}"
        if "HX-Target" in request.headers and request.headers["HX-Target"] == "feature_sigreo-table":
            return render(
                request,
                "search/v1/partials/_feature_sig_reg_effects_table.html",
                {"sig_reg_effects": sig_reos_page, "content_query": content_query},
            )

        if "HX-Target" in request.headers and request.headers["HX-Target"] == "feature-sig-reg-effects":
            return render(
                request,
                "search/v1/partials/_feature_sig_reg_effects_content.html",
                {"sig_reg_effects": sig_reos_page, "content_query": content_query},
            )

        return super().get(
            request,
            options,
            {"sig_reg_effects": sig_reos_page, "content_query": content_query},
        )

    def get_tsv(self, request, options, data):
        region = options["region"]
        if is_bed6(options):
            filename = f"significant_reos_{region.chromo}_{region.range.lower}_{region.range.upper}.bed"
        else:
            filename = f"significant_reos_{region.chromo}_{region.range.lower}_{region.range.upper}.tsv"
        return super().get_tsv(request, options, data, filename=filename)

    def get_data(self, options):
        region, assembly, features, facets = (
            options["region"],
            options["assembly"],
            options["features"],
            options["facets"],
        )

        if self.request.user.is_anonymous:
            sig_reos = Search.feature_sig_reos(region, assembly, features, facets)
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            sig_reos = Search.feature_sig_reos(region, assembly, features, facets, UserType.ADMIN)
        else:
            sig_reos = Search.feature_sig_reos(
                region,
                assembly,
                features,
                facets,
                UserType.LOGGED_IN,
                private_experiments=self.request.user.all_experiments(),
            )
        return sig_reos
