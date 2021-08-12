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
def gene(request, id_type, id):
    search_type = request.GET.get("search_type", "exact")
    search_results = GeneSearch.id_search(id_type, id, search_type)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse([json(result) for result in search_results], safe=False)

    if id_type == IdType.ENSEMBL.value:
        gene = search_results.prefetch_related("transcript_set", "dnaseihypersensitivesite_set", "assemblies").first()
        return render(
            request,
            "search/gene_exact.html",
            {
                "gene": gene,
                "assemblies": gene.assemblies,
                "transcripts": gene.transcript_set,
                "dhss": gene.dnaseihypersensitivesite_set,
            },
        )
    else:
        return render(request, "search/genes.html", {"genes": search_results})


# @method_decorator(csrf_exempt, name='dispatch') # only needed for POST, in dev.
def gene_loc(request, chr, start, end):
    search_type = request.GET.get("search_type", "exact")
    assembly = request.GET.get("assembly", None)
    search_results = GeneSearch.loc_search(chr, start, end, assembly, search_type)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse([json(result) for result in search_results], safe=False)

    return render(request, "search/genes.html", {"genes": search_results})


@singledispatch
def json(model):
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
def _(gene):
    return {
        "ensembl_id": gene.ensembl_id,
        "type": gene.gene_type,
        "locations": [json(assembly) for assembly in gene.assemblies.all()],
    }
