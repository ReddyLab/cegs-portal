from functools import singledispatch

from django.http.response import JsonResponse
from django.shortcuts import render

from cegs_portal.search.models import Experiment
from cegs_portal.search.view_models import ExperimentSearch
from cegs_portal.search.views.view_utils import JSON_MIME


def experiment(request, exp_id):
    search_result = ExperimentSearch.id_search(exp_id)

    if request.headers.get("accept") == JSON_MIME:
        return JsonResponse(json(search_result), safe=False)

    return render(request, "search/experiment.html", {"experiment": search_result})


@singledispatch
def json(_model):
    pass


@json.register(Experiment)
def _(experiment_obj):
    return {"id": experiment_obj.id, "name": experiment_obj.name}
