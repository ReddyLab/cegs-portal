from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import View


class RequestExperimentDataView(View, LoginRequiredMixin):
    """
    Kick off the task to pull experiment data from the DB
    for later download
    """

    def post(self, *args, **kwargs):

        file_url = reverse("get_expr_data:experimentdata", args=["fileurl"])
        check_completion_url = "check_completion_url"
        return JsonResponse(
            {
                "file location": file_url,
                "file progress": check_completion_url,
            }
        )
