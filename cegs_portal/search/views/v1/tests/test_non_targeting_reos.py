import json
from typing import cast

import pytest
from django.test import Client

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import DNAFeature

pytestmark = pytest.mark.django_db


def test_sig_only_proximal_reg_effects_list_json(client: Client, proximal_non_targeting_reg_effects):
    source = proximal_non_targeting_reg_effects["source"]
    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = client.get(f"/search/regeffect/nontarget/{source.closest_gene.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 2  # Only the significant effects

    for json_reo, reo in zip(json_content["object_list"], effects):
        assert json_reo["accession_id"] == reo.accession_id
        assert json_reo["effect_size"] == reo.effect_size
        assert json_reo["direction"] == reo.direction
        assert json_reo["significance"] == reo.significance
        assert json_reo["direction"] != "Non-significant"


def test_proximal_reg_effects_list_json(client: Client, proximal_non_targeting_reg_effects):
    source = proximal_non_targeting_reg_effects["source"]
    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = client.get(
        f"/search/regeffect/nontarget/{source.closest_gene.accession_id}?sig_only=false&accept=application/json"
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == len(effects)  # all the effects


def test_get_proximal_reg_effects_with_anonymous_client(client: Client, private_proximal_non_targeting_reg_effects):
    source = private_proximal_non_targeting_reg_effects["source"]
    response = client.get(f"/search/regeffect/nontarget/{source.closest_gene.accession_id}?accept=application/json")
    assert response.status_code == 302


def test_get_proximal_reg_effects_with_authenticated_client(
    login_client: SearchClient, private_proximal_non_targeting_reg_effects
):
    source = private_proximal_non_targeting_reg_effects["source"]
    response = login_client.get(
        f"/search/regeffect/nontarget/{source.closest_gene.accession_id}?accept=application/json"
    )
    assert response.status_code == 403


def test_get_proximal_reg_effects_with_authenticated_authorized_client(
    login_client: SearchClient, private_proximal_non_targeting_reg_effects
):
    source = private_proximal_non_targeting_reg_effects["source"]
    private_gene = source.closest_gene
    login_client.set_user_experiments([private_gene.experiment_accession])
    response = login_client.get(f"/search/regeffect/nontarget/{private_gene.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_get_proximal_reg_effects_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/regeffect/nontarget/{private_feature.accession_id}?accept=application/json"
    )
    assert response.status_code == 200


def test_get_archived_proximal_reg_effects_with_anonymous_client(client: Client, archived_feature: DNAFeature):
    response = client.get(f"/search/regeffect/nontarget/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_proximal_reg_effects_with_authenticated_client(
    login_client: SearchClient, archived_feature: DNAFeature
):
    response = login_client.get(f"/search/regeffect/nontarget/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_proximal_reg_effects_with_authenticated_authorized_client(
    login_client: SearchClient, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    login_client.set_user_experiments([cast(str, archived_feature.experiment_accession)])
    response = login_client.get(f"/search/regeffect/nontarget/{archived_feature.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_get_archived_proximal_reg_effects_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/regeffect/nontarget/{archived_feature.accession_id}?accept=application/json"
    )
    assert response.status_code == 403


def test_proximal_reg_effects_list_page_json(client: Client, proximal_non_targeting_reg_effects):
    source = proximal_non_targeting_reg_effects["source"]
    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = client.get(
        f"/search/regeffect/nontarget/{source.closest_gene.accession_id}?accept=application/json&page=1&per_page=1"
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 1
    assert json_content["num_pages"] == 2

    json_reo = json_content["object_list"][0]
    reo = effects[0]

    assert json_reo["accession_id"] == reo.accession_id
    assert json_reo["effect_size"] == reo.effect_size
    assert json_reo["direction"] == reo.direction
    assert json_reo["significance"] == reo.significance


def test_source_regeffect_html(client: Client, feature: DNAFeature):
    response = client.get(f"/search/regeffect/nontarget/{feature.accession_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200
