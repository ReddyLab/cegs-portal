from functools import singledispatch

from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.models import Gene, GeneAssembly
from cegs_portal.search.view_models import GeneSearch, IdType
from cegs_portal.search.views.utils import integerRangeDict

# from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import csrf_exempt


JSON_MIME = "application/json"


# @method_decorator(csrf_exempt, name='dispatch')
def gene(request, id_type, gene_id):
    search_type = request.GET.get("search_type", "exact")
    search_results = GeneSearch.id_search(id_type, gene_id, search_type)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse([json(result) for result in search_results], safe=False)

    if id_type == IdType.ENSEMBL.value:
        gene_obj = search_results.prefetch_related(
            "transcript_set", "dnaseihypersensitivesite_set", "assemblies"
        ).first()
        return render(
            request,
            "search/gene_exact.html",
            {
                "gene": gene_obj,
                "assemblies": gene_obj.assemblies,
                "transcripts": gene_obj.transcript_set,
                "dhss": gene_obj.dnaseihypersensitivesite_set,
            },
        )

    return render(request, "search/genes.html", {"genes": search_results})


# @method_decorator(csrf_exempt, name='dispatch') # only needed for POST, in dev.
def gene_loc(request, chromo, start, end):
    search_type = request.GET.get("search_type", "exact")
    assembly = request.GET.get("assembly", None)

    if chromo.isnumeric():
        chromo = f"chr{chromo}"

    search_results = GeneSearch.loc_search(chromo, start, end, assembly, search_type)

    if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
        results = [json(result) for result in search_results]

        if request.GET.get("format", None) == "genoverse":
            for result in results:
                genoverse_reformat(result)

        return JsonResponse(results, safe=False)

    return render(request, "search/genes.html", {"genes": search_results})


def genoverse_reformat(gene_dict):
    gene_dict["id"] = str(gene_dict["id"])
    gene_dict["chr"] = gene_dict["chr"].removeprefix("chr")
    gene_dict["start"] = gene_dict["location"]["start"]
    gene_dict["end"] = gene_dict["location"]["end"]
    del gene_dict["location"]


@singledispatch
def json(_model):
    pass


@json.register(GeneAssembly)
def _(gene_assembly):
    return {
        "name": gene_assembly.name,
        "chr": gene_assembly.chrom_name,
        "location": integerRangeDict(gene_assembly.location),
        "strand": gene_assembly.strand,
        "ids": gene_assembly.ids,
        "ref_genome": gene_assembly.ref_genome,
        "ref_genome_patch": gene_assembly.ref_genome_patch,
    }


@json.register(Gene)
def _(gene_obj):
    return {
        "ensembl_id": gene_obj.ensembl_id,
        "type": gene_obj.gene_type,
        "locations": [json(assembly) for assembly in gene_obj.assemblies.all()],
    }
