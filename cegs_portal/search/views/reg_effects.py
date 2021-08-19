from functools import singledispatch

from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.models import DNaseIHypersensitiveSite, RegulatoryEffect
from cegs_portal.search.view_models import DHSSearch
from cegs_portal.search.views.utils import integerRangeDict

JSON_MIME = "application/json"


def dhs(request, dhs_id):
    search_results = DHSSearch.id_search(dhs_id)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_results), safe=False)

    return render(request, "search/dhs_exact.html", {"dhs": search_results})


def dhs_loc(request, chromo, start, end):
    search_type = request.GET.get("search_type", "exact")
    assembly = request.GET.get("assembly", None)
    search_results = DHSSearch.loc_search(chromo, start, end, assembly, search_type)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse([json(result) for result in search_results], safe=False)

    return render(request, "search/dhs.html", {"dhss": search_results})


@singledispatch
def json(_model):
    pass


@json.register(DNaseIHypersensitiveSite)
def _(dhs_object):
    return {
        "id": dhs_object.id,
        "cell_line": dhs_object.cell_line,
        "chr": dhs_object.chromosome_name,
        "location": integerRangeDict(dhs_object.location),
        "strand": dhs_object.strand,
        "closest_gene": dhs_object.closest_gene.ensembl_id,
        "ref_genome": dhs_object.ref_genome,
        "ref_genome_patch": dhs_object.ref_genome_patch,
        "regulatory_effects": [json(effect) for effect in dhs_object.regulatory_effects.all()],
    }


@json.register(RegulatoryEffect)
def _(reg_effect):
    return {
        "id": reg_effect.id,
        "direction": reg_effect.direction,
        "score": reg_effect.score,
        "significance": reg_effect.significance,
        "targets": [target.ensemble_id for target in reg_effect.targets.all()],
    }
