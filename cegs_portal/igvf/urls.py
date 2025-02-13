from django.urls import re_path

from cegs_portal.igvf.views import CoverageView

app_name = "igvf"
urlpatterns = [
    re_path(r"coverage/(?P<exp_id>DCPEXPR[A-F0-9]{8,10})$", view=CoverageView.as_view(), name="coverage"),
]
