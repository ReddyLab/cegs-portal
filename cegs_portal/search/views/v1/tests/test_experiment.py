import json
from typing import Tuple

import pytest
from django.test import Client

from cegs_portal.search.models import Experiment
from cegs_portal.utils.pagination_types import Pageable

pytestmark = pytest.mark.django_db


def test_experiment_list_json(client: Client, paged_experiments: Pageable[Experiment]):
    response = client.get("/search/experiment?accept=application/json")
    paged_experiments.paginator.per_page = 20  # The default number
    experiments = paged_experiments.paginator.page(1)
    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == len(experiments.object_list)

    for json_expr, expr in zip(json_content["object_list"], experiments.object_list):
        assert json_expr["accession_id"] == expr.accession_id
        assert json_expr["name"] == expr.name
        assert json_expr["description"] == expr.description


def test_experiment_list_json_page(client: Client, paged_experiments: Pageable[Experiment]):
    page = 2
    response = client.get(
        f"/search/experiment?accept=application/json&page={page}&per_page={paged_experiments.paginator.per_page}"
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    experiments = paged_experiments.paginator.page(page)

    assert len(json_content["object_list"]) == len(experiments.object_list)

    for json_expr, expr in zip(json_content["object_list"], experiments.object_list):
        assert json_expr["accession_id"] == expr.accession_id
        assert json_expr["name"] == expr.name
        assert json_expr["description"] == expr.description


def test_experiment_list_html(client: Client):
    response = client.get("/search/experiment")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_experiment_list_with_anonymous_client(client: Client, access_control_experiments: Tuple[Experiment]):
    response = client.get("/search/experiment?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["object_list"]) == 1


def test_experiment_list_with_authenticated_client(
    client: Client, access_control_experiments: Tuple[Experiment], django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get("/search/experiment?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["object_list"]) == 1


def test_experiment_list_with_authenticated_authorized_client(
    client: Client, access_control_experiments: Tuple[Experiment], django_user_model
):
    _, private_experiment, archived_experiment = access_control_experiments
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [private_experiment.accession_id, archived_experiment.accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get("/search/experiment?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["object_list"]) == 2


def test_experiment_json(client: Client, experiment: Experiment):
    response = client.get(f"/search/experiment/{experiment.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["accession_id"] == experiment.accession_id
    assert json_content["name"] == experiment.name
    assert json_content["description"] == experiment.description


def test_experiment_html(client: Client, experiment: Experiment):
    response = client.get(f"/search/experiment/{experiment.accession_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_no_experiment_html(client: Client):
    response = client.get("/search/experiment/DCPEXPR00000000")

    assert response.status_code == 404


def test_experiment_with_anonymous_client(client: Client, private_experiment: Experiment):
    response = client.get(f"/search/experiment/{private_experiment.accession_id}?accept=application/json")
    assert response.status_code == 302


def test_experiment_with_authenticated_client(client: Client, private_experiment: Experiment, django_user_model):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/experiment/{private_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_experiment_with_authenticated_authorized_client(
    client: Client, private_experiment: Experiment, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [private_experiment.accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/experiment/{private_experiment.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_archived_experiment_with_anonymous_client(client: Client, archived_experiment: Experiment):
    response = client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_experiment_with_authenticated_client(
    client: Client, archived_experiment: Experiment, django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_experiment_with_authenticated_authorized_client(
    client: Client, archived_experiment: Experiment, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [archived_experiment.accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403
