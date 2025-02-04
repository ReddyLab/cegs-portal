from django.urls import path

from cegs_portal.igvf.views import CoverageView

app_name = "igvf"
urlpatterns = [
    path("coverage", view=CoverageView.as_view(), name="coverage"),
]
