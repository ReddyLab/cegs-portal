import json

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db

# These tests should simulate the endpoint calls that genoverse makes and ensure that the
# data genoverse needs is included


def functional_characterization_test(client: Client, genoverse_features, fcp_type):
    chrom = genoverse_features["chrom"]
    assembly = genoverse_features["ref_genome"]
    start = genoverse_features["start"]
    end = genoverse_features["end"]
    features = genoverse_features["features"]

    response = client.get(
        f"/search/featureloc/{chrom}/{start + 100}/{end - 100}?assembly={assembly}&search_type=overlap&accept=application/json&format=genoverse&feature_type=DHS&feature_type=cCRE&property=effect_directions&property=significant&property={fcp_type[0]}"  # noqa: E501
    )

    assert response.status_code == 200

    json_content = json.loads(response.content)
    for f in features:
        for r in f.source_for.all():
            print(r.facet_values.all())
    assert isinstance(json_content, list)
    assert len(json_content) == len(
        [
            f
            for f in features
            if len(f.source_for.all()) > 0
            and all(
                all(s.value != "Non-significant" for s in r.facet_values.all())
                and any(s.value == fcp_type[1] for s in r.facet_values.all())
                for r in f.source_for.all()
            )
        ]
    )

    effectful_dhs = [f for f in json_content if len(f["effect_directions"]) > 0]
    for dhs in effectful_dhs:
        assert "chr" in dhs
        assert "start" in dhs
        assert "end" in dhs

    for feature in json_content:
        assert "accession_id" in feature


def test_genoverse_track_model_reporter_assay(client: Client, genoverse_features):
    for fc in [("reporterassay", "Reporter Assay"), ("crispri", "CRISPRi"), ("crispra", "CRISPRa")]:
        functional_characterization_test(client, genoverse_features, fc)


def test_genoverse_track_view_cCRE(client: Client, genoverse_features):
    chrom = genoverse_features["chrom"]
    assembly = genoverse_features["ref_genome"]
    start = genoverse_features["start"]
    end = genoverse_features["end"]

    response = client.get(
        f"/search/featureloc/{chrom}/{start + 100}/{end - 100}?assembly={assembly}&search_type=overlap&accept=application/json&format=genoverse&feature_type=cCRE&property=screen_ccre"  # noqa: E501
    )

    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert isinstance(json_content, list)
    assert len(json_content) == 2
    for feature in json_content:
        assert feature["type"] == "cCRE"
        assert feature.get("ccre_type", None) is not None


def test_genoverse_track_model_gene_portal(client: Client, genoverse_gene_features):
    chrom = genoverse_gene_features["chrom"]
    assembly = genoverse_gene_features["ref_genome"]
    start = genoverse_gene_features["start"]
    end = genoverse_gene_features["end"]
    features = genoverse_gene_features["features"]

    response = client.get(
        f"/search/featureloc/{chrom}/{start + 100}/{end - 100}?assembly={assembly}&accept=application/json&format=genoverse&feature_type=Gene"  # noqa: E501
    )

    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert isinstance(json_content, list)
    assert len(json_content) == len(features)

    for feature in json_content:
        assert feature.get("strand", None) is not None
        assert feature.get("name", None) is not None
        assert feature.get("ensembl_id", None) is not None


def test_genoverse_track_model_transcript_portal(client: Client, genoverse_transcript_features):
    chrom = genoverse_transcript_features["chrom"]
    assembly = genoverse_transcript_features["ref_genome"]
    start = genoverse_transcript_features["start"]
    end = genoverse_transcript_features["end"]
    features = genoverse_transcript_features["features"]

    response = client.get(
        f"/search/featureloc/{chrom}/{start + 100}/{end - 100}?assembly={assembly}&accept=application/json&format=genoverse&feature_type=Transcript&feature_type=Exon&property=parent_info"  # noqa: E501
    )

    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert isinstance(json_content, list)
    assert len(json_content) == len(features)

    transcripts = [f for f in json_content if f["type"] == "transcript"]
    exons = [f for f in json_content if f["type"] == "exon"]

    for transcript in transcripts:
        assert transcript.get("id", None) is not None
        assert transcript.get("accession_id", None) is not None
        assert transcript.get("strand", None) is not None
        assert transcript.get("name", None) is not None
        assert transcript.get("ensembl_id", None) is not None
        assert transcript.get("subtype", None) is not None
        assert transcript.get("start", None) is not None
        assert transcript.get("parent", None) is not None
        assert transcript.get("parent_accession_id", None) is not None
        assert transcript.get("parent_ensembl_id", None) is not None
        assert transcript["parent_subtype"] is not None

    for exon in exons:
        assert exon.get("parent_accession_id", None) is not None
