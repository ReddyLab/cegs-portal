import json
import re
from typing import cast

import pytest
from django.test import Client

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import RegulatoryEffectObservation

pytestmark = pytest.mark.django_db


def check_tsv_response(response, features, reo):
    assert response.status_code == 200
    response_tsv = response.content.decode("utf-8")
    assert len(features) > 0

    for feature in features:
        match feature.strand:
            case "+":
                strand = r"\+"
            case None:
                strand = "."
            case "-":
                strand = "-"
        gene_dist = feature.closest_gene_distance if feature.closest_gene_distance is not None else ""
        name = feature.name if feature.name is not None else ""
        line = f"{feature.chrom_name}\t{feature.location.lower}\t{feature.location.upper}\t{feature.chrom_name}:{feature.location.lower}-{feature.location.upper}:{strand}:{name}\t0\t{strand}\t{gene_dist}\t{feature.get_feature_type_display()}\t{feature.accession_id}\t{reo.effect_size}\t{reo.direction}\t{reo.significance}\t{feature.experiment_accession_id}"
        assert re.search(line, response_tsv) is not None


def check_bed_response(response, features):
    assert response.status_code == 200
    response_tsv = response.content.decode("utf-8")
    assert len(features) > 0

    for feature in features:
        match feature.strand:
            case "+":
                strand = r"\+"
            case None:
                strand = "."
            case "-":
                strand = "-"
        name = feature.name if feature.name is not None else ""
        line = f"{feature.chrom_name}\t{feature.location.lower}\t{feature.location.upper}\t{feature.chrom_name}:{feature.location.lower}-{feature.location.upper}:{strand}:{name}\t0\t{strand}"
        assert re.search(line, response_tsv) is not None


def test_regeffect_json(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(f"/search/regeffect/{reg_effect.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["accession_id"] == reg_effect.accession_id
    assert json_content["direction"] == reg_effect.direction
    assert json_content["effect_size"] == reg_effect.effect_size
    assert json_content["significance"] == reg_effect.significance


def test_regeffect_html(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(f"/search/regeffect/{reg_effect.accession_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_no_regeffect_html(client: Client):
    response = client.get("/search/regeffect/DCPREO0000000000")

    assert response.status_code == 404


def test_regeffect_accession_with_anonymous_client(client: Client, private_reg_effect: RegulatoryEffectObservation):
    response = client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 302


def test_regeffect_accession_with_authenticated_client(
    login_client: SearchClient, private_reg_effect: RegulatoryEffectObservation
):
    response = login_client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_regeffect_accession_with_authenticated_authorized_client(
    login_client: SearchClient, private_reg_effect: RegulatoryEffectObservation
):
    login_client.set_user_experiments([private_reg_effect.experiment_accession])
    response = login_client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_regeffect_accession_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, private_reg_effect: RegulatoryEffectObservation
):
    assert private_reg_effect.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, private_reg_effect.experiment_accession_id)])
    response = group_login_client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_archived_regeffect_accession_with_anonymous_client(
    client: Client, archived_reg_effect: RegulatoryEffectObservation
):
    response = client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_regeffect_accession_with_authenticated_client(
    login_client: Client, archived_reg_effect: RegulatoryEffectObservation
):
    response = login_client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_regeffect_accession_with_authenticated_authorized_client(
    login_client: Client, archived_reg_effect: RegulatoryEffectObservation
):
    login_client.set_user_experiments([archived_reg_effect.experiment_accession])
    response = login_client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_regeffect_accession_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, archived_reg_effect: RegulatoryEffectObservation
):
    group_login_client.set_group_experiments([archived_reg_effect.accession_id])
    response = group_login_client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_reo_sources_tsv(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(
        f"/search/regeffect/{reg_effect.accession_id}/sources?accept=text/tab-separated-values"  # noqa: E501
    )
    check_tsv_response(response, reg_effect.sources.all(), reg_effect)


def test_reo_sources_bed(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(
        f"/search/regeffect/{reg_effect.accession_id}/sources?accept=text/tab-separated-values&tsv_format=bed6"  # noqa: E501 # noqa: E501
    )
    check_bed_response(response, reg_effect.sources.all())


def test_reo_targets_tsv(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(
        f"/search/regeffect/{reg_effect.accession_id}/targets?accept=text/tab-separated-values"  # noqa: E501
    )
    check_tsv_response(response, reg_effect.targets.all(), reg_effect)


def test_reo_targets_bed(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(
        f"/search/regeffect/{reg_effect.accession_id}/targets?accept=text/tab-separated-values&tsv_format=bed6"  # noqa: E501 # noqa: E501
    )
    check_bed_response(response, reg_effect.targets.all())
