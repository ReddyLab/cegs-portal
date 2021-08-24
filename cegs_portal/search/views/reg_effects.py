from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import DHSSearch, GeneSearch
from cegs_portal.search.views.renderers import genoverse_reformat, json

JSON_MIME = "application/json"


def dhs(request, dhs_id):
    """
    Headers used:
        accept
            * application/json
    """
    search_results = DHSSearch.id_search(dhs_id)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_results), safe=False)

    return render(request, "search/dhs_exact.html", {"dhs": search_results})


def dhs_loc(request, chromo, start, end):
    """
    Headers used:
        accept
            * application/json
    GET queries used:
        accept
            * application/json
        format
            * genoverse, only relevant for json
        search_type
            * exact
            * overlap
        assembly
            * free-text, but should match a genome assembly that exists in the DB
        extended
            * a flag, only relevant for json
    """
    search_type = request.GET.get("search_type", "exact")
    assembly = request.GET.get("assembly", None)

    if chromo.isnumeric():
        chromo = f"chr{chromo}"

    dhs_list = DHSSearch.loc_search(chromo, start, end, assembly, search_type)

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        return dhs_loc_json(request, dhs_list, request.GET.get("extended", False))

    gene_ids = [dhs.closest_gene_id for dhs in dhs_list]
    closest_genes = GeneSearch.id_search("db", gene_ids, "in")
    closest_gene_dict = {gene.id: gene for gene in closest_genes}

    closest_genes = [closest_gene_dict[gene_id] for gene_id in gene_ids]
    dhss = list(zip(dhs_list, closest_genes))

    return render(request, "search/dhs.html", {"dhss": dhss, "loc": {"chr": chromo, "start": start, "end": end}})


def dhs_loc_json(request, dhs_list, extended):
    results = [json(result) for result in dhs_list]

    closest_gene_dict = {}
    closest_genes = []
    if extended:
        gene_ids = [dhs.closest_gene_id for dhs in dhs_list]
        closest_genes = GeneSearch.id_search("db", gene_ids, "in")
        closest_gene_dict = {gene.id: json(gene) for gene in closest_genes}

    if request.GET.get("format", None) == "genoverse":
        for result in results:
            genoverse_reformat(result)
        for gene_id in closest_gene_dict:
            genoverse_reformat(closest_gene_dict[gene_id])

    for dhs_json in results:
        dhs_json["closest_gene"] = closest_gene_dict.get(dhs_json["closest_gene"], dhs_json["closest_gene"])

    return JsonResponse(results, safe=False)
