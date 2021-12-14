from django.urls import path

from . import views

app_name = "search"
urlpatterns = [
    path("", views.index, name="index"),
    path("results/", views.v1.SearchView.as_view(), name="results"),
    path("feature/ensembl/<str:feature_id>", views.v1.FeatureEnsembl.as_view(), name="feature_ensembl"),
    path("feature/<str:id_type>/<str:feature_id>", views.v1.Feature.as_view(), name="features"),
    path("featureloc/<str:chromo>/<int:start>/<int:end>", views.v1.FeatureLoc.as_view(), name="feature_loc"),
    path("dhs/<int:dhs_id>", views.v1.DHS.as_view(), name="dhs"),
    path("dhsloc/<str:chromo>/<int:start>/<int:end>", views.v1.DHSLoc.as_view(), name="dhs_loc"),
    path("experiment/<int:exp_id>", views.v1.ExperimentView.as_view(), name="experiment"),
    path("regeffect/<int:re_id>", views.v1.RegEffectView.as_view(), name="reg_effect"),
    path("v1/results/", views.v1.SearchView.as_view(), name="results"),
    path("v1/feature/ensembl/<str:feature_id>", views.v1.FeatureEnsembl.as_view(), name="feature_ensembl"),
    path("v1/feature/<str:id_type>/<str:feature_id>", views.v1.Feature.as_view(), name="features"),
    path("v1/featureloc/<str:chromo>/<int:start>/<int:end>", views.v1.FeatureLoc.as_view(), name="feature_loc"),
    path("v1/dhs/<int:dhs_id>", views.v1.DHS.as_view(), name="dhs"),
    path("v1/dhsloc/<str:chromo>/<int:start>/<int:end>", views.v1.DHSLoc.as_view(), name="dhs_loc"),
    path("v1/experiment/<int:exp_id>", views.v1.ExperimentView.as_view(), name="experiment"),
    path("v1/regeffect/<int:re_id>", views.v1.RegEffectView.as_view(), name="reg_effect"),
]
