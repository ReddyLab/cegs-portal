import re
from typing import Optional

from django.db import models
from django.db.models import Prefetch, Q

from cegs_portal.search.models import (
    ChromosomeLocation,
    DNARegion,
    Facet,
    RegulatoryEffect,
)
from cegs_portal.search.models.utils import QueryToken

CHROMO_RE = re.compile(r"\b((chr[12]?[123456789xym])\s*:\s*(\d+)(-(\d+))?)\b", re.IGNORECASE)
ENSEMBL_RE = re.compile(r"\b(ENS[0-9a-z]+)", re.IGNORECASE)
# HAVANA_RE = re.compile(r"\b(OTT[0-9a-z]+)", re.IGNORECASE)
# HUGO_RE = re.compile(r"\b(HGNC:[0-9a-z]+)", re.IGNORECASE)
ASSEMBLY_RE = re.compile(r"\b(hg19|hg38|grch37|grch38)\b", re.IGNORECASE)
GENE_NAME_RE = re.compile(r"\b([A-Z0-9][A-Z0-9\.\-]+)\b", re.IGNORECASE)


def parse_query(query: str) -> tuple[list[tuple[QueryToken, str]], Optional[ChromosomeLocation], str, list[str]]:
    terms: list[tuple[QueryToken, str]] = []
    assembly = None
    location = None
    gene_names = []

    for result in re.finditer(CHROMO_RE, query):
        location = ChromosomeLocation(result.group(2), result.group(3), result.group(5))
    query = re.sub(CHROMO_RE, " ", query)

    for result in re.finditer(ENSEMBL_RE, query):
        terms.append(QueryToken.ENSEMBL_ID.associate(result.group(1)))
    query = re.sub(ENSEMBL_RE, " ", query)

    assembly = "GRCh38"  # Default
    for result in re.finditer(ASSEMBLY_RE, query):
        token = result.group(1).lower()

        # Normalize token
        if token == "hg19" or token == "grch37":
            token = "GRCh37"
        elif token == "hg38" or token == "grch38":
            token = "GRCh38"
        assembly = token
    query = re.sub(ASSEMBLY_RE, " ", query)

    for result in re.finditer(GENE_NAME_RE, query):
        gene_names.append(result.group(1))

    return terms, location, assembly, gene_names


class Search:
    @classmethod
    def _dnaregion_search(
        cls, location: ChromosomeLocation, assembly: str, facets: list[int], region_type: Optional[list[str]] = None
    ):
        q = Q(chromosome_name=location.chromo, location__overlap=location.range, ref_genome=assembly)
        q &= Q(regulatory_effects__count__gt=0)

        if len(facets) > 0:
            q &= Q(facet_values__in=facets)

        if region_type is not None:
            q &= Q(region_type__in=region_type)

        sig_effects = RegulatoryEffect.objects.exclude(direction__exact="non_sig").prefetch_related(
            "targets",
            "targets__parent",
            "target_assemblies",
            "target_assemblies__feature",
            "target_assemblies__feature__parent",
        )

        return (
            DNARegion.objects.annotate(models.Count("regulatory_effects"))
            .prefetch_related(Prefetch("regulatory_effects", queryset=sig_effects), "facet_values")
            .filter(q)
            .select_related(
                "closest_gene",
                "closest_gene__parent",
                "closest_gene_assembly",
                "closest_gene_assembly__feature",
                "closest_gene_assembly__feature__parent",
            )
        )

    @classmethod
    def search(cls, query_string: str, facets: list[int] = []):
        _query_terms, location, assembly_name, gene_names = parse_query(query_string)
        sites = None
        if location is not None:
            sites = cls._dnaregion_search(location, assembly_name, facets, region_type=["dhs"])
        facet_results = Facet.objects.all().prefetch_related("values")

        return {
            "loc_search": {
                "location": location,
                "assembly": assembly_name,
            },
            "dhss": sites,
            "facets": facet_results,
        }
