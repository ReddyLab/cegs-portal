import pytest
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.views.v1 import FeatureCountView

pytestmark = pytest.mark.django_db


@pytest.fixture
def feature_count_view():
    return FeatureCountView.as_view()


@pytest.mark.usefixtures("dna_features")
def test_feature_counts_e2e(client: Client):
    response = client.get("/search/feature_counts?region=chr1%3A1-1000000")
    assert response.status_code == 200

    response = client.get("/search/feature_counts?region=chr1%3A1-1000000&&assembly=hg19")
    assert response.status_code == 200


@pytest.mark.usefixtures("dna_features")
def test_feature_counts(public_test_client: RequestBuilder, feature_count_view):
    response = public_test_client.get("/search/feature_counts?region=chr1%3A1-1000000").request(feature_count_view)
    assert response.status_code == 200


@pytest.mark.usefixtures("dna_features")
def test_feature_counts_with_assembly(public_test_client: RequestBuilder, feature_count_view):
    response = public_test_client.get("/search/feature_counts?region=chr1%3A1-1000000&&assembly=hg19").request(
        feature_count_view
    )
    assert response.status_code == 200


@pytest.mark.usefixtures("dna_features")
def test_feature_counts_json(public_test_client: RequestBuilder, feature_count_view):
    response = public_test_client.get("/search/feature_counts?region=chr1%3A1-1000000&accept=application/json").request(
        feature_count_view
    )
    assert response.status_code == 200

    json_content = response.json()
    assert json_content["region"] == {"chromo": "chr1", "start": 1, "end": 1000000}
    assert json_content["assembly"] == "hg38"
    assert json_content["counts"] == [
        {"feature_type": "Experimentally Tested Element", "count": 2, "sig_reo_count": 2},
        {"feature_type": "Gene", "count": 2, "sig_reo_count": 1},
        {"feature_type": "Transcript", "count": 0, "sig_reo_count": 0},
        {"feature_type": "Exon", "count": 0, "sig_reo_count": 0},
        {"feature_type": "cCRE", "count": 1, "sig_reo_count": 0},
    ]


@pytest.mark.usefixtures("dna_features_hg19")
def test_feature_counts_with_assembly_json(public_test_client: RequestBuilder, feature_count_view):
    response = public_test_client.get(
        "/search/feature_counts?region=chr1%3A1-1000000&assembly=hg19&accept=application/json"
    ).request(feature_count_view)
    assert response.status_code == 200

    json_content = response.json()
    assert json_content["region"] == {"chromo": "chr1", "start": 1, "end": 1000000}
    assert json_content["assembly"] == "hg19"
    assert json_content["counts"] == [
        {"feature_type": "Experimentally Tested Element", "count": 2, "sig_reo_count": 2},
        {"feature_type": "Gene", "count": 2, "sig_reo_count": 1},
        {"feature_type": "Transcript", "count": 0, "sig_reo_count": 0},
        {"feature_type": "Exon", "count": 0, "sig_reo_count": 0},
        {"feature_type": "cCRE", "count": 1, "sig_reo_count": 0},
    ]
