from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.view_models import ExperimentSearch
from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


def experiment(request, exp_id):
    experi = ExperimentSearch.id_search(exp_id)

    experi_cell_lines = set()
    experi_tissue_types = set()
    experi_assemblies = set()
    for f in experi.data_files.all():
        experi_cell_lines.update(f.cell_lines.all())
        experi_tissue_types.update(f.tissue_types.all())
        experi_assemblies.add(f"{f.ref_genome}.{f.ref_genome_patch or '0'}")

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(experi), safe=False)

    return render(
        request,
        "search/experiment.html",
        {
            "experiment": experi,
            "cell_lines": experi_cell_lines,
            "tissue_types": experi_tissue_types,
            "assemblies": experi_assemblies,
        },
    )
