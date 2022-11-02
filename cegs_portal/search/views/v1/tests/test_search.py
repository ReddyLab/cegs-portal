import json

import pytest
from django.test import Client

from cegs_portal.search.models import DNAFeature

pytestmark = pytest.mark.django_db


def test_experiment_json(client: Client):
    response = client.get("/search/results/?query=chr1%3A0-1000000+hg19&accept=application/json")

    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert json_content["location"] == {
        "assembly": "GRCh37",
        "chromosome": "chr1",
        "start": 0,
        "end": 1_000_000,
    }
    assert len(json_content["features"]) == 0


def test_experiment_feature_json(client: Client, feature: DNAFeature):
    response = client.get(
        f"/search/results/?query={feature.chrom_name}%3A{feature.location.lower - 10}-{feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["location"] == {
        "assembly": None,
        "chromosome": feature.chrom_name,
        "start": feature.location.lower - 10,
        "end": feature.location.upper + 10,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_json(client: Client, feature: DNAFeature):
    response = client.get(f"/search/results/?query={feature.accession_id}&accept=application/json")  # noqa: E501

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["location"] == {
        "assembly": feature.ref_genome,
        "chromosome": feature.chrom_name,
        "start": max(0, feature.location.lower - 1000),
        "end": feature.location.upper + 1000,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_json(client: Client, feature: DNAFeature):
    response = client.get(f"/search/results/?query={feature.ensembl_id}&accept=application/json")  # noqa: E501

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["location"] == {
        "assembly": feature.ref_genome,
        "chromosome": feature.chrom_name,
        "start": max(0, feature.location.lower - 1000),
        "end": feature.location.upper + 1000,
    }
    assert len(json_content["features"]) == 1


def test_experiment_html(client: Client):
    response = client.get("/search/results/?query=chr1%3A0-1000000")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_experiment_no_query_json(client: Client):
    response = client.get("/search/results/?accept=application/json")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 400


def test_experiment_no_query_html(client: Client):
    response = client.get("/search/results/")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 400
