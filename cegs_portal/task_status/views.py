from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator

from cegs_portal.search.views.custom_views import MultiResponseFormatView

from .json_templates.task_status import task_statuses


def get_bool_param(value):
    if value == "0" or value == "false" or value == "False":
        return False
    else:
        return True


class TaskStatusView(UserPassesTestMixin, MultiResponseFormatView):
    json_renderer = task_statuses
    template = "task_status/task_status.html"

    def test_func(self):
        if self.request.user.is_anonymous:
            return False

        if self.request.user.username != self.kwargs["username"]:
            return False

        return True

    def request_options(self, request):
        """
        GET queries used:
            paginate - only used for JSON data, HTML is always paginated
            page - which page to show
                * int
        """
        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        options["paginate"] = get_bool_param(request.GET.get("paginate", True))
        return options

    def get(self, request, options, data, username):
        return super().get(request, options, {"tasks": data, "per_page": options["per_page"]})

    def get_data(self, options, username):
        tasks = self.request.user.tasks.all().order_by("-created")
        if options["paginate"]:
            tasks_paginator = Paginator(tasks, options["per_page"])
            tasks_data = tasks_paginator.get_page(options["page"])
        else:
            tasks_data = tasks
        return tasks_data
