import re

from cegs_portal.search.models import (
    ChromosomeLocation,
    DNARegion,
    Feature,
    FeatureAssembly,
)
from cegs_portal.search.models.reg_effects import RegulatoryEffect
from cegs_portal.search.models.utils import QueryToken

CHROMO_RE = re.compile(r"(chr[12]?[123456789xym]):(\d+)(-(\d+))?", re.IGNORECASE)
ENSEMBL_RE = re.compile(r"ENS[0-9a-z]+", re.IGNORECASE)
HAVANA_RE = re.compile(r"OTT[0-9a-z]+", re.IGNORECASE)
HUGO_RE = re.compile(r"HGNC:[0-9a-z]+", re.IGNORECASE)
ASSEMBLY_RE = re.compile(r"hg19|hg38|grch37|grch38", re.IGNORECASE)


def parse_query(query):
    terms: list[tuple[QueryToken, str]] = []
    assembly = None
    location = None
    tokens: list[str] = query.split()

    for token in tokens:
        if result := CHROMO_RE.match(token):
            location = ChromosomeLocation(result.group(1), result.group(2), result.group(4))
        elif result := ENSEMBL_RE.match(token):
            terms.append(QueryToken.ENSEMBL_ID.associate(token))
        elif result := ASSEMBLY_RE.match(token):
            token = token.lower()

            # Normalize token
            if token == "hg19" or token == "grch37":
                token = "GRCh37"
            elif token == "hg38" or token == "grch38":
                token = "GRCh38"
            assembly = token
    return terms, location, assembly


class Search:
    @classmethod
    def search(cls, query_string):
        query_terms, location, assembly_name = parse_query(query_string)
        feature_assembly_dict: dict[Feature, list[FeatureAssembly]] = {}
        targeting_effects_dict: dict[Feature, list[RegulatoryEffect]] = {}

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

        features = Feature.search(query_terms)

        sites = DNARegion.search(location)
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
