from django.shortcuts import render

from cegs_portal.search.forms import SearchForm
from cegs_portal.search.tasks import count_beans


def index(request):
    rsp = count_beans(12)
    print(rsp)
    form = SearchForm()
    return render(request, "search/index.html", {"form": form})
