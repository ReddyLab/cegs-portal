from functools import singledispatch

from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.models import DNaseIHypersensitiveSite, RegulatoryEffect
from cegs_portal.search.view_models import DHSSearch, GeneSearch
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

    if chromo.isnumeric():
        chromo = f"chr{chromo}"

    dhs_list = DHSSearch.loc_search(chromo, start, end, assembly, search_type)

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        results = [json(result) for result in dhs_list]

        if request.GET.get("format", None) == "genoverse":
            for result in results:
                genoverse_reformat(result)

        return JsonResponse(results, safe=False)

    gene_ids = [dhs.closest_gene_id for dhs in dhs_list]
    closest_genes = GeneSearch.id_search("db", gene_ids, "in", distinct=False)
    closest_gene_dict = {gene.id: gene for gene in closest_genes}
    closest_genes = [closest_gene_dict[gene_id] for gene_id in gene_ids]

    dhss = list(zip(dhs_list, closest_genes))

    return render(request, "search/dhs.html", {"dhss": dhss, "loc": {"chr": chromo, "start": start, "end": end}})


def genoverse_reformat(dhs_dict):
    dhs_dict["id"] = str(dhs_dict["id"])
    dhs_dict["chr"] = dhs_dict["chr"].removeprefix("chr")
    dhs_dict["start"] = dhs_dict["location"]["start"]
    dhs_dict["end"] = dhs_dict["location"]["end"]
    del dhs_dict["location"]


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
