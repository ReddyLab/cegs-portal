from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = "search"
urlpatterns = [
    path("", views.index, name="index"),
    path("results/", views.v1.SearchView.as_view(), name="results"),
    path("feature/ensembl/<str:feature_id>", views.v1.FeatureEnsembl.as_view(), name="feature_ensembl"),
    path("feature/<str:id_type>/<str:feature_id>", views.v1.Feature.as_view(), name="features"),
    path("featureloc/<str:chromo>/<int:start>/<int:end>", views.v1.FeatureLoc.as_view(), name="feature_loc"),
    path("region/<int:region_id>", views.v1.DNARegion.as_view(), name="region"),
    path("regionloc/<str:chromo>/<int:start>/<int:end>", views.v1.DNARegionLoc.as_view(), name="region_loc"),
    path("experiment", views.v1.ExperimentListView.as_view(), name="experiments"),
    path("experiment/<str:exp_id>", views.v1.ExperimentView.as_view(), name="experiment"),
    path("regeffect/region/<int:region_id>", views.v1.RegionEffectsView.as_view(), name="region_effects"),
    path("regeffect/<int:re_id>", views.v1.RegEffectView.as_view(), name="reg_effect"),
    path("v1/results/", views.v1.SearchView.as_view()),
    path("v1/feature/ensembl/<str:feature_id>", views.v1.FeatureEnsembl.as_view()),
    path("v1/feature/<str:id_type>/<str:feature_id>", views.v1.Feature.as_view()),
    path("v1/featureloc/<str:chromo>/<int:start>/<int:end>", views.v1.FeatureLoc.as_view()),
    path("v1/region/<int:region_id>", views.v1.DNARegion.as_view()),
    path("v1/regionloc/<str:chromo>/<int:start>/<int:end>", views.v1.DNARegionLoc.as_view()),
    path("v1/experiment", views.v1.ExperimentListView.as_view()),
    path("v1/experiment/<str:exp_id>", views.v1.ExperimentView.as_view()),
    path("v1/regeffect/region/<int:region_id>", views.v1.RegionEffectsView.as_view()),
    path("v1/regeffect/<int:re_id>", views.v1.RegEffectView.as_view()),
] + static("v1/", document_root=str(settings.APPS_DIR / "search" / "static" / "search" / "v1"))
