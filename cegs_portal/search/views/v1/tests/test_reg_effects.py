import json
from typing import cast

import pytest
from django.test import Client

from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.users.models import GroupExtension

pytestmark = pytest.mark.django_db


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
    response = client.get("/search/regeffect/DCPREO00000000")

    assert response.status_code == 404


def test_regeffect_accession_with_anonymous_client(client: Client, private_reg_effect: RegulatoryEffectObservation):
    response = client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 302


def test_regeffect_accession_with_authenticated_client(
    client: Client, private_reg_effect: RegulatoryEffectObservation, django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_regeffect_accession_with_authenticated_authorized_client(
    client: Client, private_reg_effect: RegulatoryEffectObservation, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [private_reg_effect.experiment_accession]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_regeffect_accession_with_authenticated_authorized_group_client(
    client: Client, private_reg_effect: RegulatoryEffectObservation, group_extension: GroupExtension, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)

    assert private_reg_effect.experiment_accession_id is not None

    group_extension.experiments = [cast(str, private_reg_effect.experiment_accession_id)]
    group_extension.save()
    user.groups.add(group_extension.group)
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/regeffect/{private_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_archived_regeffect_accession_with_anonymous_client(
    client: Client, archived_reg_effect: RegulatoryEffectObservation
):
    response = client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_regeffect_accession_with_authenticated_client(
    client: Client, archived_reg_effect: RegulatoryEffectObservation, django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_regeffect_accession_with_authenticated_authorized_client(
    client: Client, archived_reg_effect: RegulatoryEffectObservation, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [archived_reg_effect.experiment_accession]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_regeffect_accession_with_authenticated_authorized_group_client(
    client: Client, archived_reg_effect: RegulatoryEffectObservation, group_extension: GroupExtension, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    group_extension.experiments = [archived_reg_effect.accession_id]
    group_extension.save()
    user.groups.add(group_extension.group)
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/regeffect/{archived_reg_effect.accession_id}?accept=application/json")
    assert response.status_code == 403
