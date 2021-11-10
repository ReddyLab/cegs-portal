import re
from typing import Optional

from cegs_portal.search.models import (
    ChromosomeLocation,
    DNARegion,
    Feature,
    FeatureAssembly,
)
from cegs_portal.search.models.reg_effects import RegulatoryEffect
from cegs_portal.search.models.utils import QueryToken

CHROMO_RE = re.compile(r"\b((chr[12]?[123456789xym])\s*:\s*(\d+)(-(\d+))?)\b", re.IGNORECASE)
ENSEMBL_RE = re.compile(r"\b(ENS[0-9a-z]+)", re.IGNORECASE)
# HAVANA_RE = re.compile(r"\b(OTT[0-9a-z]+)", re.IGNORECASE)
# HUGO_RE = re.compile(r"\b(HGNC:[0-9a-z]+)", re.IGNORECASE)
ASSEMBLY_RE = re.compile(r"\b(hg19|hg38|grch37|grch38)\b", re.IGNORECASE)
GENE_NAME_RE = re.compile(r"\b([A-Z0-9][A-Z0-9\.\-]+)\b", re.IGNORECASE)


def parse_query(query: str) -> tuple[list[QueryToken], Optional[ChromosomeLocation], Optional[str], list[str]]:
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
    def search(cls, query_string):
        query_terms, location, assembly_name, gene_names = parse_query(query_string)
        feature_assembly_dict: dict[Feature, list[FeatureAssembly]] = {}
        targeting_effects_dict: dict[Feature, list[RegulatoryEffect]] = {}
        sites = None
        if location is not None:
            feature_assemblies = FeatureAssembly.search(location, assembly_name, feature_types=["gene"])
            feature_assemblies.prefetch_related("regulatory_effects")
            # Inverts the feature/assembly relationship
            for assembly in feature_assemblies:
                assemblies = feature_assembly_dict.get(assembly.feature, [])
                assemblies.append(assembly)
                feature_assembly_dict[assembly.feature] = assemblies

                reg_effects = targeting_effects_dict.get(assembly.feature, [])
                reg_effects.extend(assembly.regulatory_effects.all())
                targeting_effects_dict[assembly.feature] = reg_effects
            sites = DNARegion.search(location)

        features = Feature.search(query_terms)

        return {
            "loc_search": {
                "location": location,
                "assembly": assembly_name,
                "features": feature_assembly_dict,
                "targeting_effects": targeting_effects_dict,
            },
            "features": features,
            "dhss": sites,
        }

    def facets(self):
        pass
