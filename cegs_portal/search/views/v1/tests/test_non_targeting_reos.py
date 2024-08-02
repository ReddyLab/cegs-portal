import json
from typing import cast

import pytest
from django.core.exceptions import PermissionDenied
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.models import DNAFeature
from cegs_portal.search.views.v1 import NonTargetRegEffectsView

pytestmark = pytest.mark.django_db


@pytest.fixture
def view():
    return NonTargetRegEffectsView.as_view()


def test_sig_only_proximal_reg_effects_list_e2e(client: Client, proximal_non_targeting_reg_effects):
    source = proximal_non_targeting_reg_effects["source"]
    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = client.get(
        f"/search/feature/accession/{source.closest_gene.accession_id}/nontargets?accept=application/json"
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 2  # Only the significant effects

    for json_reo, reo in zip(json_content["object_list"], effects):
        assert json_reo["accession_id"] == reo.accession_id
        assert json_reo["effect_size"] == reo.effect_size
        assert json_reo["direction"] == reo.direction
        assert json_reo["significance"] == reo.significance
        assert json_reo["direction"] != "Non-significant"

    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = client.get(
        f"/search/feature/accession/{source.closest_gene.accession_id}/nontargets?sig_only=false&accept=application/json"
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == len(effects)  # all the effects


def test_sig_only_proximal_reg_effects_list_json(
    public_test_client: RequestBuilder, view, proximal_non_targeting_reg_effects
):
    source = proximal_non_targeting_reg_effects["source"]
    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = public_test_client.get(
        f"/search/feature/accession/{source.closest_gene.accession_id}/nontargets?accept=application/json"
    ).request(view, feature_id=source.closest_gene.accession_id)

    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["object_list"]) == 2  # Only the significant effects

    for json_reo, reo in zip(json_content["object_list"], effects):
        assert json_reo["accession_id"] == reo.accession_id
        assert json_reo["effect_size"] == reo.effect_size
        assert json_reo["direction"] == reo.direction
        assert json_reo["significance"] == reo.significance
        assert json_reo["direction"] != "Non-significant"


def test_proximal_reg_effects_list_json(public_test_client: RequestBuilder, view, proximal_non_targeting_reg_effects):
    source = proximal_non_targeting_reg_effects["source"]
    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = public_test_client.get(
        f"/search/feature/accession/{source.closest_gene.accession_id}/nontargets?sig_only=false&accept=application/json"
    ).request(view, feature_id=source.closest_gene.accession_id)

    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["object_list"]) == len(effects)  # all the effects


def test_get_proximal_reg_effects_with_anonymous_client(
    public_test_client: RequestBuilder, view, private_proximal_non_targeting_reg_effects
):
    source = private_proximal_non_targeting_reg_effects["source"]
    response = public_test_client.get(
        f"/search/feature/accession/{source.closest_gene.accession_id}/nontargets?accept=application/json"
    ).request(view, feature_id=source.closest_gene.accession_id)
    assert response.status_code == 302


def test_get_proximal_reg_effects_with_authenticated_client(
    login_test_client: RequestBuilder, view, private_proximal_non_targeting_reg_effects
):
    source = private_proximal_non_targeting_reg_effects["source"]
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{source.closest_gene.accession_id}/nontargets?accept=application/json"
        ).request(view, feature_id=source.closest_gene.accession_id)


def test_get_proximal_reg_effects_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, view, private_proximal_non_targeting_reg_effects
):
    source = private_proximal_non_targeting_reg_effects["source"]
    private_gene = source.closest_gene
    login_test_client.set_user_experiments([private_gene.experiment_accession_id])
    response = login_test_client.get(
        f"/search/feature/accession/{private_gene.accession_id}/nontargets?accept=application/json"
    ).request(view, feature_id=private_gene.accession_id)
    assert response.status_code == 200


def test_get_proximal_reg_effects_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, view, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])
    response = group_login_test_client.get(
        f"/search/feature/accession/{private_feature.accession_id}/nontargets?accept=application/json"
    ).request(view, feature_id=private_feature.accession_id)
    assert response.status_code == 200


def test_get_archived_proximal_reg_effects_with_anonymous_client(
    public_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        public_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/nontargets?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_get_archived_proximal_reg_effects_with_authenticated_client(
    login_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/nontargets?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_get_archived_proximal_reg_effects_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    login_test_client.set_user_experiments([cast(str, archived_feature.experiment_accession)])
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/nontargets?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_get_archived_proximal_reg_effects_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])
    with pytest.raises(PermissionDenied):
        group_login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}/nontargets?accept=application/json"
        ).request(view, feature_id=archived_feature.accession_id)


def test_proximal_reg_effects_list_page_json(
    public_test_client: RequestBuilder, view, proximal_non_targeting_reg_effects
):
    source = proximal_non_targeting_reg_effects["source"]
    effects = sorted(proximal_non_targeting_reg_effects["effects"], key=lambda x: x.significance)
    response = public_test_client.get(
        f"/search/feature/accession/{source.closest_gene.accession_id}/nontargets?accept=application/json&page=1&per_page=1"
    ).request(view, feature_id=source.closest_gene.accession_id)

    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["object_list"]) == 1
    assert json_content["num_pages"] == 2

    json_reo = json_content["object_list"][0]
    reo = effects[0]

    assert json_reo["accession_id"] == reo.accession_id
    assert json_reo["effect_size"] == reo.effect_size
    assert json_reo["direction"] == reo.direction
    assert json_reo["significance"] == reo.significance


def test_source_regeffect_html(public_test_client: RequestBuilder, view, feature: DNAFeature):
    response = public_test_client.get(f"/search/feature/accession/{feature.accession_id}/nontargets").request(
        view, feature_id=feature.accession_id
    )

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200
