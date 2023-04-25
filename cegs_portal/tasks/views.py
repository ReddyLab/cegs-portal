import logging

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.tasks.json_templates.v1 import task
from cegs_portal.tasks.view_models import ThreadTaskSearch

logger = logging.getLogger("django.request")


class TaskStatusView(UserPassesTestMixin, TemplateJsonView):
    json_renderer = task
    template = "tasks/v1/task_status.html"
    template_data_name = "task"

    def test_func(self):
        # Only portal admins should have access to tasks
        user = self.request.user
        # An anonymous user won't have the is_portal_admin property, but also definitely isn't
        # a portal admin.
        return not user.is_anonymous and user.is_portal_admin

    def get_data(self, _options, task_id):
        try:
            return ThreadTaskSearch.id_search(task_id)
        except ObjectDoesNotExist as e:
            raise Http404() from e
