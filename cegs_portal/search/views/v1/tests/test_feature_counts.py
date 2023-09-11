import json

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("dna_features")
def test_feature_counts(client: Client):
    response = client.get("/search/feature_counts?region=chr1%3A1-1000000")
    assert response.status_code == 200


@pytest.mark.usefixtures("dna_features")
def test_feature_counts_with_assembly(client: Client):
    response = client.get("/search/feature_counts?region=chr1%3A1-1000000&&assembly=hg19")
    assert response.status_code == 200


@pytest.mark.usefixtures("dna_features")
def test_feature_counts_json(client: Client):
    response = client.get("/search/feature_counts?region=chr1%3A1-1000000&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert json_content["region"] == {"chromo": "chr1", "start": 1, "end": 1000000}
    assert json_content["assembly"] == "GRCh38"
    assert json_content["counts"] == [
        {"feature_type": "Experiment Regulatory Effect Source", "count": 2, "sig_reo_count": 2},
        {"feature_type": "Gene", "count": 2, "sig_reo_count": 1},
        {"feature_type": "Transcript", "count": 0, "sig_reo_count": 0},
        {"feature_type": "Exon", "count": 0, "sig_reo_count": 0},
        {"feature_type": "cCRE", "count": 1, "sig_reo_count": 0},
    ]


@pytest.mark.usefixtures("dna_features_grch37")
def test_feature_counts_with_assembly_json(client: Client):
    response = client.get("/search/feature_counts?region=chr1%3A1-1000000&assembly=hg19&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert json_content["region"] == {"chromo": "chr1", "start": 1, "end": 1000000}
    assert json_content["assembly"] == "GRCh37"
    assert json_content["counts"] == [
        {"feature_type": "Experiment Regulatory Effect Source", "count": 2, "sig_reo_count": 2},
        {"feature_type": "Gene", "count": 2, "sig_reo_count": 1},
        {"feature_type": "Transcript", "count": 0, "sig_reo_count": 0},
        {"feature_type": "Exon", "count": 0, "sig_reo_count": 0},
        {"feature_type": "cCRE", "count": 1, "sig_reo_count": 0},
    ]
