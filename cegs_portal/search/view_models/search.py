import re

from cegs_portal.search.models import (
    ChromosomeLocation,
    DNaseIHypersensitiveSite,
    Gene,
    GeneAssembly,
)
from cegs_portal.search.models.utils import QueryToken

CHROMO_RE = re.compile(r"(chr[12]?[123456789xym]):(\d+)(-(\d+))?", re.IGNORECASE)
ENSEMBL_RE = re.compile(r"ENS[0-9a-z]+", re.IGNORECASE)
HAVANA_RE = re.compile(r"OTT[0-9a-z]+", re.IGNORECASE)
HUGO_RE = re.compile(r"HGNC:[0-9a-z]+", re.IGNORECASE)


def parse_query(query):
    terms = []
    tokens = query.split()
    for token in tokens:
        if result := CHROMO_RE.match(token):
            location = ChromosomeLocation(result.group(1), result.group(2), result.group(4))
            terms.append(QueryToken.LOCATION.associate(location))
        elif result := ENSEMBL_RE.match(token):
            terms.append(QueryToken.ENSEMBL_ID.associate(token))
    return terms


class Search:
    @classmethod
    def search(cls, query_string):
        parse_result = parse_query(query_string)
        assemblies = GeneAssembly.search(parse_result)
        sites = DNaseIHypersensitiveSite.search(parse_result)
        genes = Gene.search(parse_result)
        return {"assemblies": assemblies, "genes": genes, "dh_sites": sites}

    def facets(self):
        pass
