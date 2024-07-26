from typing import Any

import pytest
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.models import Experiment
from cegs_portal.search.views.v1.experiment import ExperimentListView

pytestmark = pytest.mark.django_db


@pytest.fixture
def experiment_list_view():
    return ExperimentListView.as_view()


def test_experiment_list(client: Client):
    response = client.get("/search/experiment")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200

    response = client.get("/search/experiment?accept=application/json")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_experiment_list_json(
    public_test_client: RequestBuilder, experiment_list_view, experiment_list_data: tuple[Any, Any]
):
    experiments, _ = experiment_list_data
    response = public_test_client.get("/search/experiment?accept=application/json").request(experiment_list_view)
    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["experiments"]) == len(experiments)

    for json_expr, expr in zip(json_content["experiments"], experiments):
        assert json_expr["accession_id"] == expr.accession_id
        assert json_expr["name"] == expr.name
        assert json_expr["description"] == (expr.description if expr.description is not None else "")


def test_experiment_list_facet_json(
    public_test_client: RequestBuilder, experiment_list_view, experiment_list_data: tuple[Any, Any]
):
    _, facets = experiment_list_data
    response = public_test_client.get(f"/search/experiment?accept=application/json&facet={facets[0].id}").request(
        experiment_list_view
    )
    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["experiments"]) == 3


def test_experiment_list_all_facets_json(
    public_test_client: RequestBuilder, experiment_list_view, experiment_list_data: tuple[Any, Any]
):
    experiments, facets = experiment_list_data
    response = public_test_client.get(
        f"/search/experiment?accept=application/json&facet={facets[0].id}&facet={facets[1].id}"
    ).request(experiment_list_view)
    assert response.status_code == 200
    json_content = response.json()

    assert len(json_content["experiments"]) == len(experiments)


def test_experiment_list_html(public_test_client: RequestBuilder, experiment_list_view):
    response = public_test_client.get("/search/experiment").request(experiment_list_view)

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


@pytest.mark.usefixtures("access_control_experiments")
def test_experiment_list_with_anonymous_client(public_test_client: RequestBuilder, experiment_list_view):
    response = public_test_client.get("/search/experiment?accept=application/json").request(experiment_list_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["experiments"]) == 1


@pytest.mark.usefixtures("access_control_experiments")
def test_experiment_list_with_authenticated_client(login_test_client: RequestBuilder, experiment_list_view):
    response = login_test_client.get("/search/experiment?accept=application/json").request(experiment_list_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["experiments"]) == 1


def test_experiment_list_with_authenticated_authorized_client(
    login_test_client: RequestBuilder,
    experiment_list_view,
    access_control_experiments: tuple[Experiment, Experiment, Experiment],
):
    _, private_experiment, archived_experiment = access_control_experiments

    login_test_client.set_user_experiments([private_experiment.accession_id, archived_experiment.accession_id])
    response = login_test_client.get("/search/experiment?accept=application/json").request(experiment_list_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["experiments"]) == 2


def test_experiment_list_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder,
    experiment_list_view,
    access_control_experiments: tuple[Experiment, Experiment, Experiment],
):
    _, private_experiment, archived_experiment = access_control_experiments

    group_login_test_client.set_group_experiments([private_experiment.accession_id, archived_experiment.accession_id])
    response = group_login_test_client.get("/search/experiment?accept=application/json").request(experiment_list_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["experiments"]) == 2
