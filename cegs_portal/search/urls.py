from django.urls import path

from . import views

app_name = "search"
urlpatterns = [
    path("", views.index, name="index"),
    path("results/", views.results, name="results"),
    path("gene/<str:id_type>/<str:id>", views.gene, name="genes"),
    path("geneloc/<str:chr>/<int:start>/<int:end>", views.gene_loc, name="gene_loc"),
    path("dhs/<int:id>", views.dhs, name="dhs"),
    path("dhsloc/<str:chr>/<int:start>/<int:end>", views.dhs_loc, name="dhs_loc"),
    path("experiment/<int:id>", views.experiment, name="experiment"),
]
