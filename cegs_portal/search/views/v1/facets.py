from django.shortcuts import render

from cegs_portal.search.models import Facet


def facets(request):
    facets = Facet.objects.filter(facet_type="FacetType.CATEGORICAL").order_by("name").prefetch_related("values")
    return render(request, "search/v1/facets.html", {"facets": facets})
