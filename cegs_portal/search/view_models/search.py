import re

from cegs_portal.search.models import (
    ChromosomeLocation,
    DNaseIHypersensitiveSite,
    GencodeGFF3Entry,
)

CHROMO_RE = re.compile(r"(chr[12]?[123456789xXyYmM]):(\d+)(-(\d+))?")


def parse_query(query):
    terms = []
    tokens = query.split()
    for token in tokens:
        if result := CHROMO_RE.match(token):
            location = ChromosomeLocation(result.group(1), result.group(2), result.group(4))
            terms.append(location)
    return terms


class Search:
    @classmethod
    def search(cls, query_string):
        parse_result = parse_query(query_string)
        entries = GencodeGFF3Entry.search(parse_result)
        annotations = {entry.annotation for entry in entries}
        sites = DNaseIHypersensitiveSite.search(parse_result)
        return {"annotations": annotations, "dh_sites": sites}

    def facets(self):
        pass
