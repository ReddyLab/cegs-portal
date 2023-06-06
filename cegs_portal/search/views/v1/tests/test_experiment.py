import json
from typing import Any

import pytest
from django.test import Client

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import Experiment

pytestmark = pytest.mark.django_db


def test_experiment_list_json(client: Client, experiment_list_data: tuple[Any, Any]):
    response = client.get("/search/experiment?accept=application/json")
    experiments, _ = experiment_list_data
    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["experiments"]) == len(experiments)

    for json_expr, expr in zip(json_content["experiments"], experiments):
        assert json_expr["accession_id"] == expr.accession_id
        assert json_expr["name"] == expr.name
        assert json_expr["description"] == expr.description


def test_experiment_list_html(client: Client):
    response = client.get("/search/experiment")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


@pytest.mark.usefixtures("access_control_experiments")
def test_experiment_list_with_anonymous_client(client: Client):
    response = client.get("/search/experiment?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["experiments"]) == 1


@pytest.mark.usefixtures("access_control_experiments")
def test_experiment_list_with_authenticated_client(login_client: SearchClient):
    response = login_client.get("/search/experiment?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["experiments"]) == 1


def test_experiment_list_with_authenticated_authorized_client(
    login_client: SearchClient, access_control_experiments: tuple[Experiment, Experiment, Experiment]
):
    _, private_experiment, archived_experiment = access_control_experiments

    login_client.set_user_experiments([private_experiment.accession_id, archived_experiment.accession_id])
    response = login_client.get("/search/experiment?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["experiments"]) == 2


def test_experiment_list_with_authenticated_authorized_group_client(
    group_login_client: Client, access_control_experiments: tuple[Experiment, Experiment, Experiment]
):
    _, private_experiment, archived_experiment = access_control_experiments

    group_login_client.set_group_experiments([private_experiment.accession_id, archived_experiment.accession_id])
    response = group_login_client.get("/search/experiment?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["experiments"]) == 2


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


def test_experiment_with_authenticated_client(login_client: SearchClient, private_experiment: Experiment):
    response = login_client.get(f"/search/experiment/{private_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_experiment_with_authenticated_authorized_client(login_client: SearchClient, private_experiment: Experiment):
    login_client.set_user_experiments([private_experiment.accession_id])
    response = login_client.get(f"/search/experiment/{private_experiment.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_experiment_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, private_experiment: Experiment
):
    group_login_client.set_group_experiments([private_experiment.accession_id])
    response = group_login_client.get(f"/search/experiment/{private_experiment.accession_id}?accept=application/json")
    assert response.status_code == 200


def test_archived_experiment_with_anonymous_client(client: Client, archived_experiment: Experiment):
    response = client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_experiment_with_authenticated_client(login_client: SearchClient, archived_experiment: Experiment):
    response = login_client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_experiment_with_authenticated_authorized_client(
    login_client: SearchClient, archived_experiment: Experiment
):
    login_client.set_user_experiments([archived_experiment.accession_id])
    response = login_client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403


def test_archived_experiment_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, archived_experiment: Experiment
):
    group_login_client.set_group_experiments([archived_experiment.accession_id])
    response = group_login_client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json")
    assert response.status_code == 403
