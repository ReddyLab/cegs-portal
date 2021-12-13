from django.urls import path

from . import views

app_name = "search"
urlpatterns = [
    path("", views.index, name="index"),
    path("results/", views.results, name="results"),
    path("feature/ensembl/<str:feature_id>", views.FeatureEnsembl.as_view(), name="features"),
    path("feature/<str:id_type>/<str:feature_id>", views.feature, name="features"),
    path("featureloc/<str:chromo>/<int:start>/<int:end>", views.FeatureLoc.as_view(), name="feature_loc"),
    path("dhs/<int:dhs_id>", views.DHS.as_view(), name="dhs"),
    path("dhsloc/<str:chromo>/<int:start>/<int:end>", views.DHSLoc.as_view(), name="dhs_loc"),
    path("experiment/<int:exp_id>", views.ExperimentView.as_view(), name="experiment"),
    path("regeffect/<int:re_id>", views.RegEffectView.as_view(), name="reg_effect"),
]
