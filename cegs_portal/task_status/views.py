from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

from cegs_portal.search.views.custom_views import MultiResponseFormatView
from cegs_portal.utils import truthy_to_bool

from .json_templates.task_status import task_status, task_statuses
from .view_models import get_status


class TaskStatusView(UserPassesTestMixin, MultiResponseFormatView):
    json_renderer = task_status
    template = "task_status/task_status.html"

    def test_func(self):
        if self.request.user.is_anonymous:
            return False

        return True

    def get(self, request, options, data, task_id):
        return super().get(request, options, {"task": data})

    def get_data(self, options, task_id):
        task = get_status(task_id)
        if task is None or task.user != self.request.user:
            raise PermissionDenied(f"User does not have permission for task {task_id}")

        return task


class TaskStatusListView(UserPassesTestMixin, MultiResponseFormatView):
    json_renderer = task_statuses
    template = "task_status/task_status_list.html"

    def test_func(self):
        if self.request.user.is_anonymous:
            return False

        if self.request.user.username != self.kwargs["username"]:
            return False

        return True

    def request_options(self, request):
        """
        GET queries used:
            page - which page to show
                * int
            per_page - how many items to show per page
            paginate - only used for JSON data, HTML is always paginated
        """
        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))
        options["per_page"] = int(request.GET.get("per_page", 20))
        options["paginate"] = truthy_to_bool(request.GET.get("paginate", True))
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
