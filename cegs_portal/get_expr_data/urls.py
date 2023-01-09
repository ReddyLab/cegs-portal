from django.urls import path, re_path

from cegs_portal.get_expr_data.views import RequestExperimentDataView

app_name = "get_expr_data"
urlpatterns = [
    path("request", view=RequestExperimentDataView.as_view(), name="requestdata"),
    re_path(r"file/(?P<file_name>\w+)$", view=RequestExperimentDataView.as_view(), name="experimentdata"),
]
