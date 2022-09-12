from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = "search"
urlpatterns = [
    path("", views.index, name="index"),
    path("results/", views.v1.SearchView.as_view(), name="results"),
    path("feature/ensembl/<str:feature_id>", views.v1.DNAFeatureEnsembl.as_view(), name="dna_feature_ensembl"),
    path("feature/<str:id_type>/<str:feature_id>", views.v1.DNAFeatureId.as_view(), name="dna_features"),
    path("featureloc/<str:chromo>/<int:start>/<int:end>", views.v1.DNAFeatureLoc.as_view(), name="dna_feature_loc"),
    path("experiment", views.v1.ExperimentListView.as_view(), name="experiments"),
    path("experiment/<str:exp_id>", views.v1.ExperimentView.as_view(), name="experiment"),
    path(
        "experiment_coverage",
        csrf_exempt(views.v1.ExperimentCoverageView.as_view()),
        name="experiment_coverage",
    ),
    path("regeffect/source/<str:source_id>", views.v1.SourceEffectsView.as_view(), name="source_effects"),
    path("regeffect/<str:re_id>", views.v1.RegEffectView.as_view(), name="reg_effect"),
    path("v1/results/", views.v1.SearchView.as_view()),
    path("v1/feature/ensembl/<str:feature_id>", views.v1.DNAFeatureEnsembl.as_view()),
    path("v1/feature/<str:id_type>/<str:feature_id>", views.v1.DNAFeatureId.as_view()),
    path("v1/featureloc/<str:chromo>/<int:start>/<int:end>", views.v1.DNAFeatureLoc.as_view()),
    path("v1/experiment", views.v1.ExperimentListView.as_view()),
    path("v1/experiment/<str:exp_id>", views.v1.ExperimentView.as_view()),
    path(
        "v1/experiment_coverage",
        csrf_exempt(views.v1.ExperimentCoverageView.as_view()),
        name="experiment_coverage",
    ),
    path("v1/regeffect/source/<str:source_id>", views.v1.SourceEffectsView.as_view()),
    path("v1/regeffect/<str:re_id>", views.v1.RegEffectView.as_view()),
] + static("v1/", document_root=str(settings.APPS_DIR / "search" / "static" / "search" / "v1"))
