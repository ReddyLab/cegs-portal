import csv

from cegs_portal.search.models import Facet, FacetValue


def run(facet_filename):
    with open(facet_filename, newline="") as facet_file:
        reader = csv.reader(facet_file, delimiter="\t")
        next(reader)  # skip the header row
        facets = []
        facet_values = []
        for row in reader:
            name, description, facet_type = row[0], row[1], row[2]
            facet = Facet(name=name, description=description, facet_type=facet_type)
            facets.append(facet)
            if facet_type == "FacetType.DISCRETE":
                for value in row[3:]:
                    facet_values.append(FacetValue(value=value, facet=facet))

        Facet.objects.bulk_create(facets)
        FacetValue.objects.bulk_create(facet_values)
