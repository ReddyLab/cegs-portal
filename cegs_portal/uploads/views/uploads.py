from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from huey.contrib.djhuey import db_task

# from cegs_portal.uploads.data_loading.analysis import load as an_load
# from cegs_portal.uploads.data_loading.experiment import load as expr_load
from cegs_portal.uploads.forms import UploadFileForm


@permission_required("search.add_experiment", raise_exception=True)
def upload(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if (experiment_file := request.FILES.get("experiment_file")) is not None:
                handle_experiment_file(request.POST["experiment_accession"], experiment_file)
            if (analysis_file := request.FILES.get("analysis_file")) is not None:
                handle_analysis_file(request.POST["experiment_accession"], analysis_file)
            return HttpResponseRedirect(reverse("uploads:upload_complete"))
    else:
        form = UploadFileForm()
    return render(request, "uploads/upload.html", {"upload_form": form})


def upload_complete(request):
    return render(request, "uploads/upload_complete.html", {})


#  Don't use these right now
@db_task
def handle_experiment_file(expr_accession, file):
    print("****************************")
    print(file)
    print(file.size)
    print("****************************")


@db_task
def handle_analysis_file(expr_accession, file):
    print("****************************")
    print(file)
    print(file.size)
    print("****************************")
