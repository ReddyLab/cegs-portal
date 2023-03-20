from django.urls import path

from cegs_portal.get_expr_data.views import (
    ExperimentDataView,
    LocationExperimentDataView,
    RequestExperimentDataView,
)

app_name = "get_expr_data"
urlpatterns = [
    path("request", view=RequestExperimentDataView.as_view(), name="requestdata"),
    path("location", view=LocationExperimentDataView.as_view(), name="locationdata"),
    path("file/<str:filename>", view=ExperimentDataView.as_view(), name="experimentdata"),
]
