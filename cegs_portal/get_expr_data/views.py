import logging
import re

# from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import View

from cegs_portal.get_expr_data.view_models import retrieve_experiment_data
from cegs_portal.utils.http_exceptions import Http400

logger = logging.getLogger("django.request")

LocList = list[tuple[str, int, int]]


def maybe_bed(file):
    return file.content_type == "text/tab-separated-values" or file.name.endswith(".bed")


def try_process_bed(bed_file) -> LocList:
    loc_list = []
    for line in bed_file:
        #  Decoding with ASCII insted of utf-8 because the text we care about should
        #  always be valid ASCII, AFAIK. If it's not, we'll update this to utf-8.
        #
        #  Not using the csv module because it expects in iterable over strings and
        #  UploadedFile (the type of the bed_file parameter) is an iterable over
        #  byte strings.
        match = re.match(r"(chr\w+)\t(\d+)\t(\d+)(\t.*)?$", line.decode("ascii"))
        if match is None:
            continue
        loc_list.append((match[1], int(match[2]), int(match[3])))

    return loc_list


class RequestExperimentDataView(View):
    """
    Kick off the task to pull experiment data from the DB
    for later download
    """

    def post(self, request, *args, **kwargs):
        try:
            file = request.FILES["regions"]
        except Exception:
            raise Http400('Invalid request; file variable name should be "region"')

        if maybe_bed(file):
            regions = try_process_bed(file)
        else:
            raise Http400(f"Invalid regions file: unknown file type for {file.name}")

        # except Exception as e:
        #     raise Http400(f"Invalid request body:\n{request.body}\n\nError:\n{e}")
        task = retrieve_experiment_data(regions)
        file_url = reverse("get_expr_data:experimentdata", args=["fileurl"])
        check_completion_url = reverse("tasks:status", args=[task.id])
        return JsonResponse(
            {
                "file location": file_url,
                "file progress": check_completion_url,
            }
        )
