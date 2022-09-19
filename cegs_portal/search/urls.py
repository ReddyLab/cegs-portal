from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = "search"
urlpatterns = [
    path("", views.index, name="index"),
    path("results/", views.v1.SearchView.as_view(), name="results"),
    re_path(
        r"feature/ensembl/(?P<feature_id>ENS[A-Z]{1,2}[0-9]{11})$",
        views.v1.DNAFeatureEnsembl.as_view(),
        name="dna_feature_ensembl",
    ),
    re_path(
        r"feature/(?P<id_type>\w+)/(?P<feature_id>DCP[A-Z]{1,4}[A-F0-9]{8})$",
        views.v1.DNAFeatureId.as_view(),
        name="dna_features",
    ),
    re_path(
        r"featureloc/(?P<chromo>(?:chr)?[a-zA-Z0-9]{1,3})/(?P<start>\d+)/(?P<end>\d+)$",
        views.v1.DNAFeatureLoc.as_view(),
        name="dna_feature_loc",
    ),
    path("experiment", views.v1.ExperimentListView.as_view(), name="experiments"),
    re_path(r"experiment/(?P<exp_id>DCPEXPR[A-F0-9]{8})$", views.v1.ExperimentView.as_view(), name="experiment"),
    path(
        "experiment_coverage",
        csrf_exempt(views.v1.ExperimentCoverageView.as_view()),
        name="experiment_coverage",
    ),
    re_path(
        r"regeffect/source/(?P<source_id>DCP[A-Z]{1,4}[A-F0-9]{8})$",
        views.v1.SourceEffectsView.as_view(),
        name="source_effects",
    ),
    re_path(r"regeffect/(?P<re_id>DCPREO[A-F0-9]{8})$", views.v1.RegEffectView.as_view(), name="reg_effect"),
    path("v1/results/", views.v1.SearchView.as_view()),
    re_path(r"v1/feature/ensembl/(?P<feature_id>ENS[A-Z]{1,2}[0-9]{11})$", views.v1.DNAFeatureEnsembl.as_view()),
    re_path(r"v1/feature/(?P<id_type>\w+)/(?P<feature_id>DCP[A-Z]]{1,4}[A-F0-9]{8})$", views.v1.DNAFeatureId.as_view()),
    re_path(
        r"v1/featureloc/(?P<chromo>(?:chr)?[a-zA-Z0-9]{1,3})/(?P<start>\d+)/(?P<end>\d+)$",
        views.v1.DNAFeatureLoc.as_view(),
    ),
    path("v1/experiment", views.v1.ExperimentListView.as_view()),
    re_path(r"v1/experiment/(?P<exp_id>DCPEXPR[A-F0-9]{8})$", views.v1.ExperimentView.as_view()),
    path(
        "v1/experiment_coverage",
        csrf_exempt(views.v1.ExperimentCoverageView.as_view()),
        name="experiment_coverage",
    ),
    re_path(r"v1/regeffect/source/(?P<source_id>DCP[A-Z]{1,4}[A-F0-9]{8})$", views.v1.SourceEffectsView.as_view()),
    re_path(r"v1/regeffect/(?P<re_id>DCPREO[A-F0-9]{8})$", views.v1.RegEffectView.as_view()),
] + static("v1/", document_root=str(settings.APPS_DIR / "search" / "static" / "search" / "v1"))
