import json
from typing import cast

import pytest
from django.test import Client

from cegs_portal.search.conftest import SearchClient
from cegs_portal.search.models import DNAFeature

pytestmark = pytest.mark.django_db


def test_target_reg_effects_list_json(client: Client, target_reg_effects):
    target = target_reg_effects["target"]
    effects = sorted(target_reg_effects["effects"], key=lambda x: x.accession_id)
    response = client.get(f"/search/regeffect/target/{target.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == len(effects)

    for json_reo, reo in zip(json_content["object_list"], effects):
        assert json_reo["accession_id"] == reo.accession_id
        assert json_reo["effect_size"] == reo.effect_size
        assert json_reo["direction"] == reo.direction
        assert json_reo["significance"] == reo.significance


def test_sig_only_target_reg_effects_list_json(client: Client, sig_only_target_reg_effects):
    target = sig_only_target_reg_effects["target"]
    response = client.get(f"/search/regeffect/target/{target.accession_id}?accept=application/json&sig_only=True")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 2

    for obj in json_content["object_list"]:
        assert(obj["direction"] != "EffectObservationDirectionType.NON_SIGNIFICANT")


def test_sig_only_false_target_reg_effects_list_json(client: Client, sig_only_target_reg_effects):
    target = sig_only_target_reg_effects["target"]
    response = client.get(f"/search/regeffect/target/{target.accession_id}?accept=application/json&sig_only=False")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    all_objects = json_content["object_list"]

    assert len(all_objects) == 4


def test_hidden_target_reg_effects_list_json(client: Client, hidden_target_reg_effects):
    target = hidden_target_reg_effects["target"]
    response = client.get(f"/search/regeffect/target/{target.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 1


def test_get_target_reg_effects_with_anonymous_client(client: Client, private_feature: DNAFeature):
    response = client.get(f"/search/regeffect/target/{private_feature.accession_id}?accept=application/json")
    assert response.status_code == 302


def test_get_target_reg_effects_with_authenticated_client(
    login_client: SearchClient, private_feature: DNAFeature, django_user_model
):
    response = login_client.get(f"/search/regeffect/target/{private_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_target_reg_effects_with_authenticated_authorized_client(
    login_client: SearchClient, private_feature: DNAFeature
):
    login_client.set_user_experiments([private_feature.experiment_accession])
    response = login_client.get(f"/search/regeffect/target/{private_feature.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_get_target_reg_effects_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/regeffect/target/{private_feature.accession_id}?accept=application/json"
    )
    assert response.status_code == 200


def test_get_archived_target_reg_effects_with_anonymous_client(client: Client, archived_feature: DNAFeature):
    response = client.get(f"/search/regeffect/target/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_target_reg_effects_with_authenticated_client(
    login_client: SearchClient, archived_feature: DNAFeature
):
    response = login_client.get(f"/search/regeffect/target/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_target_reg_effects_with_authenticated_authorized_client(
    login_client: SearchClient, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    login_client.set_user_experiments([cast(str, archived_feature.experiment_accession)])
    response = login_client.get(f"/search/regeffect/target/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_target_reg_effects_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_client.set_user_experiments([cast(str, archived_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/regeffect/target/{archived_feature.accession_id}?accept=application/json"
    )
    assert response.status_code == 403


def test_target_reg_effects_list_page_json(client: Client, target_reg_effects):
    target = target_reg_effects["target"]
    effects = sorted(target_reg_effects["effects"], key=lambda x: x.accession_id)
    response = client.get(f"/search/regeffect/target/{target.accession_id}?accept=application/json&page=1&per_page=1")

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


def test_target_regeffect_html(client: Client, feature: DNAFeature):
    response = client.get(f"/search/regeffect/target/{feature.accession_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200
