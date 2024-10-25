from typing import cast

import pytest
from django.core.exceptions import PermissionDenied
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.models import DNAFeature
from cegs_portal.search.views.v1 import SourceEffectsView

pytestmark = pytest.mark.django_db


@pytest.fixture
def view():
    return SourceEffectsView.as_view()


def test_source_reg_effects_list_e2e(client: Client, source_reg_effects, sig_only_source_reg_effects):
    source = source_reg_effects["source"]
    effects = source_reg_effects["effects"]
    response = client.get(f"/search/feature/accession/{source.accession_id}/source_for?accept=application/json")

    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["object_list"]) == len(effects)

    for json_reo, reo in zip(json_content["object_list"], effects):
        assert json_reo["accession_id"] == reo.accession_id
        assert json_reo["effect_size"] == reo.effect_size
        assert json_reo["direction"] == reo.direction
        assert json_reo["significance"] == reo.significance

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    response = client.get(f"/search/feature/accession/{source.accession_id}/source_for")

    assert response.status_code == 200


def test_sig_only_source_reg_effects(public_test_client: RequestBuilder, view, sig_only_source_reg_effects):
    source = sig_only_source_reg_effects["source"]
    response = public_test_client.get(
        f"/search/feature/accession/{source.accession_id}/source_for?accept=application/json&sig_only=True"
    ).request(view, feature_id=source.accession_id)

    assert response.status_code == 200
    json_content = response.json()

    for obj in json_content["object_list"]:
        assert obj["direction"] != "Non-significant"


def test_sig_only_false_source_reg_effects_list_json(
    public_test_client: RequestBuilder, view, sig_only_source_reg_effects
):
    source = sig_only_source_reg_effects["source"]
    response = public_test_client.get(
        f"/search/feature/accession/{source.accession_id}/source_for?accept=application/json&sig_only=False"
    ).request(view, feature_id=source.accession_id)

    assert response.status_code == 200
    json_content = response.json()

    all_objects = json_content["object_list"]

    assert len(all_objects) == 4


def test_hidden_source_reg_effects_list_json(public_test_client: RequestBuilder, view, hidden_source_reg_effects):
    source = hidden_source_reg_effects["source"]
    response = public_test_client.get(
        f"/search/feature/accession/{source.accession_id}/source_for?accept=application/json"
    ).request(view, feature_id=source.accession_id)

    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["object_list"]) == 1


def test_get_source_reg_effects_with_anonymous_client(
    public_test_client: RequestBuilder, view, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/feature/accession/{private_feature.accession_id}/source_for?accept=application/json"
    ).request(view, feature_id=private_feature.accession_id)
    assert response.status_code == 302


def test_get_source_reg_effects_with_authenticated_client(
    login_test_client: RequestBuilder, view, private_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{private_feature.accession_id}/source_for?accept=application/json"
        ).request(view, feature_id=private_feature.accession_id)


def test_get_source_reg_effects_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, view, private_feature: DNAFeature
):
    login_test_client.set_user_experiments([private_feature.experiment_accession_id])
    response = login_test_client.get(
        f"/search/feature/accession/{private_feature.accession_id}/source_for?accept=application/json"
    ).request(view, feature_id=private_feature.accession_id)
    assert response.status_code == 200


def test_get_source_reg_effects_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, view, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])
    response = group_login_test_client.get(
        f"/search/feature/accession/{private_feature.accession_id}/source_for?accept=application/json"
    ).request(view, feature_id=private_feature.accession_id)
    assert response.status_code == 200


def test_get_archived_source_reg_effects_with_anonymous_client(
    public_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        public_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/source_for?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_get_archived_source_reg_effects_with_authenticated_client(
    login_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/source_for?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_get_archived_source_reg_effects_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    login_test_client.set_user_experiments([archived_feature.experiment_accession_id])
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/source_for?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_get_archived_source_reg_effects_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([archived_feature.experiment_accession_id])
    with pytest.raises(PermissionDenied):
        group_login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/source_for?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_source_reg_effects_list_page_json(public_test_client: RequestBuilder, view, source_reg_effects):
    source = source_reg_effects["source"]
    effects = source_reg_effects["effects"]
    response = public_test_client.get(
        f"/search/feature/accession/{source.accession_id}/source_for?accept=application/json&page=1&per_page=1"
    ).request(view, feature_id=source.accession_id)

    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["object_list"]) == 1
    assert json_content["num_pages"] == 3

    json_reo = json_content["object_list"][0]
    reo = effects[0]

    assert json_reo["accession_id"] == reo.accession_id
    assert json_reo["effect_size"] == reo.effect_size
    assert json_reo["direction"] == reo.direction
    assert json_reo["significance"] == reo.significance
