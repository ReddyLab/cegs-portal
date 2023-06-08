import json
from typing import cast

import pytest
from django.test import Client

from cegs_portal.search.conftest import SearchClient
from cegs_portal.search.models import DNAFeature

pytestmark = pytest.mark.django_db


def test_source_reg_effects_list_json(client: Client, source_reg_effects):
    source = source_reg_effects["source"]
    effects = sorted(source_reg_effects["effects"], key=lambda x: x.accession_id)
    response = client.get(f"/search/regeffect/source/{source.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == len(effects)

    for json_reo, reo in zip(json_content["object_list"], effects):
        assert json_reo["accession_id"] == reo.accession_id
        assert json_reo["effect_size"] == reo.effect_size
        assert json_reo["direction"] == reo.direction
        assert json_reo["significance"] == reo.significance


def test_sig_only_source_reg_effects_list_json(client: Client, sig_only_source_reg_effects):
    source = sig_only_source_reg_effects["source"]
    response = client.get(f"/search/regeffect/source/{source.accession_id}?accept=application/json&sig_only=True")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    sig_objects = []

    for obj in json_content["object_list"]:
        if obj["direction"] != "EffectObservationDirectionType.NON_SIGNIFICANT":
            sig_objects.append(obj)


    assert len(sig_objects) == 2


def test_hidden_source_reg_effects_list_json(client: Client, hidden_source_reg_effects):
    source = hidden_source_reg_effects["source"]
    response = client.get(f"/search/regeffect/source/{source.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 1


def test_get_source_reg_effects_with_anonymous_client(client: Client, private_feature: DNAFeature):
    response = client.get(f"/search/regeffect/source/{private_feature.accession_id}?accept=application/json")
    assert response.status_code == 302


def test_get_source_reg_effects_with_authenticated_client(login_client: SearchClient, private_feature: DNAFeature):
    response = login_client.get(f"/search/regeffect/source/{private_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_source_reg_effects_with_authenticated_authorized_client(
    login_client: SearchClient, private_feature: DNAFeature
):
    login_client.set_user_experiments([private_feature.experiment_accession])
    response = login_client.get(f"/search/regeffect/source/{private_feature.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_get_source_reg_effects_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/regeffect/source/{private_feature.accession_id}?accept=application/json"
    )
    assert response.status_code == 200


def test_get_archived_source_reg_effects_with_anonymous_client(client: Client, archived_feature: DNAFeature):
    response = client.get(f"/search/regeffect/source/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_source_reg_effects_with_authenticated_client(
    login_client: SearchClient, archived_feature: DNAFeature
):
    response = login_client.get(f"/search/regeffect/source/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_source_reg_effects_with_authenticated_authorized_client(
    login_client: SearchClient, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    login_client.set_user_experiments([cast(str, archived_feature.experiment_accession)])
    response = login_client.get(f"/search/regeffect/source/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_source_reg_effects_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/regeffect/source/{archived_feature.accession_id}?accept=application/json"
    )
    assert response.status_code == 403


def test_source_reg_effects_list_page_json(client: Client, source_reg_effects):
    source = source_reg_effects["source"]
    effects = sorted(source_reg_effects["effects"], key=lambda x: x.accession_id)
    response = client.get(f"/search/regeffect/source/{source.accession_id}?accept=application/json&page=1&per_page=1")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 1
    assert json_content["num_pages"] == 3

    json_reo = json_content["object_list"][0]
    reo = effects[0]

    assert json_reo["accession_id"] == reo.accession_id
    assert json_reo["effect_size"] == reo.effect_size
    assert json_reo["direction"] == reo.direction
    assert json_reo["significance"] == reo.significance


def test_source_regeffect_html(client: Client, feature: DNAFeature):
    response = client.get(f"/search/regeffect/source/{feature.accession_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200
