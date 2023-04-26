from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView, View

from cegs_portal.get_expr_data.models import ExperimentData

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        return self.request.user.get_absolute_url()  # type: ignore [union-attr]

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


class UserDownloadsView(LoginRequiredMixin, View):
    def get(self, request, username, *args, **kwargs):
        if request.user.is_anonymous or (request.user.username != username):
            raise PermissionDenied("You do not have permission to view these downloads")

        in_prep_files = ExperimentData.objects.filter(user=request.user, state=ExperimentData.DataState.IN_PREPARATION)
        ready_files = ExperimentData.objects.filter(user=request.user, state=ExperimentData.DataState.READY)
        deleted_files = ExperimentData.objects.filter(user=request.user, state=ExperimentData.DataState.DELETED)
        return render(
            request, "users/downloads.html", {"in_prep": in_prep_files, "ready": ready_files, "deleted": deleted_files}
        )


user_downloads_view = UserDownloadsView.as_view()
