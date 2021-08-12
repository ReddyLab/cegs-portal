from functools import singledispatch

from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.models import Experiment
from cegs_portal.search.view_models import ExperimentSearch

JSON_MIME = "application/json"


def experiment(request, id):
    search_result = ExperimentSearch.id_search(id)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_result), safe=False)

    return render(request, "search/experiment.html", {"experiment": search_result})


@singledispatch
def json(model):
    pass


@json.register(Experiment)
def _(experiment):
    return {"id": experiment.id, "name": experiment.name}
