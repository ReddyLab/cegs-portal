from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import GeneSearch, IdType
from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


# @method_decorator(csrf_exempt, name='dispatch')
def gene(request, id_type, gene_id):
    """
    Headers used:
        accept
            * application/json
    GET queries used:
        accept
            * application/json
        search_type
            * exact
            * like
            * start
            * in
    """
    search_type = request.GET.get("search_type", "exact")
    search_results = GeneSearch.id_search(id_type, gene_id, search_type)

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        return JsonResponse([json(result) for result in search_results], safe=False)

    if id_type == IdType.ENSEMBL.value:
        gene_obj = search_results.prefetch_related(
            "children",
            "children__assemblies",
            "dnaregion_set",
            "dnaregion_set__regulatory_effects",
            "assemblies",
            "regulatory_effects",
            "regulatory_effects__sources",
            "regulatory_effects__experiment",
        ).first()
        return render(
            request,
            "search/feature_exact.html",
            {
                "feature": gene_obj,
                "feature_name": "Gene",
                "assemblies": gene_obj.assemblies,
                "children": gene_obj.children,
                "children_name": "Transcripts",
                "dhss": gene_obj.dnaregion_set,
                "reg_effects": gene_obj.regulatory_effects,
            },
        )

    return render(
        request,
        "search/features.html",
        {
            "features": search_results,
            "feature_name": "Genes",
        },
    )


# @method_decorator(csrf_exempt, name='dispatch') # only needed for POST, in dev.
def gene_loc(request, chromo, start, end):
    """
    Headers used:
        accept
            * application/json
    GET queries used:
        accept
            * application/json
        format
            * genoverse
        search_type
            * closest
            * exact
            * overlap
        assembly
            * free-text, but should match a genome assembly that exists in the DB
    """
    search_type = request.GET.get("search_type", "exact")
    assembly = request.GET.get("assembly", None)

    if chromo.isnumeric():
        chromo = f"chr{chromo}"

    search_results = GeneSearch.loc_search(chromo, start, end, assembly, search_type)

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        results = [json(result, request.GET.get("format", None)) for result in search_results]

        return JsonResponse(results, safe=False)

    return render(request, "search/genes.html", {"genes": search_results})
