import os.path

import pytest
from django.http import HttpResponseForbidden

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation

pytestmark = pytest.mark.django_db


def test_post_experiment_data_no_permission(login_client: SearchClient):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, "experiment.json")) as experiment:
        response = login_client.post(
            "/uploads/",
            {
                "experiment_accession": "DCPEXPR0000000000",
                "experiment_file": experiment,
                "experiment_url": [""],
                "analysis_file": [""],
                "analysis_url": [""],
            },
        )
        assert isinstance(response, HttpResponseForbidden)


def test_post_experiment_data(add_experiment_client: SearchClient):
    assert DNAFeature.objects.filter(feature_type="DNAFeatureType.DHS").count() == 0
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, "experiment.json")) as experiment:
        response = add_experiment_client.post(
            "/uploads/",
            {
                "experiment_accession": "DCPEXPR0000000000",
                "experiment_file": experiment,
                "experiment_url": [""],
                "analysis_file": [""],
                "analysis_url": [""],
            },
        )
        assert response.status_code < 400
        assert DNAFeature.objects.filter(feature_type="DNAFeatureType.DHS").count() == 10


def test_post_analysis_data(add_experiment_client: SearchClient):
    assert RegulatoryEffectObservation.objects.all().count() == 0
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_dir, "experiment.json")) as experiment, open(
        os.path.join(current_dir, "analysis001.json")
    ) as analysis:
        response = add_experiment_client.post(
            "/uploads/",
            {
                "experiment_accession": "DCPEXPR0000000000",
                "experiment_file": experiment,
                "experiment_url": [""],
                "analysis_file": analysis,
                "analysis_url": [""],
            },
        )
        assert response.status_code < 400
        assert RegulatoryEffectObservation.objects.all().count() == 14

        # Make sure that some of the DNA features get updated with information about their
        # significant REOs
        assert any(feature.significant_reo for feature in DNAFeature.objects.all())
