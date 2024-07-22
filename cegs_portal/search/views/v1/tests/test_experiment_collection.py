import pytest
from django.test import Client

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import ExperimentCollection

pytestmark = pytest.mark.django_db


def check_experiment_collection(collection: ExperimentCollection, response_json):
    assert collection.accession_id == response_json["accession_id"]
    assert collection.name == response_json["name"]
    assert collection.description == response_json["description"]


def test_experiment_collection_with_anonymous_client(experiment_collection: ExperimentCollection, client: Client):
    response = client.get(f"/search/experiment_collection/{experiment_collection.accession_id}")
    assert response.status_code == 200

    response = client.get(f"/search/experiment_collection/{experiment_collection.accession_id}?accept=application/json")
    assert response.status_code == 200

    check_experiment_collection(experiment_collection, response.json())


def test_fake_experiment_collection_with_anonymous_client(client: Client):
    response = client.get("/search/experiment_collection/DCPEXCLFFFFFFFFFF")
    assert response.status_code == 404


def test_private_experiment_collection_with_anonymous_client(
    private_experiment_collection: ExperimentCollection, client: Client
):
    response = client.get(f"/search/experiment_collection/{private_experiment_collection.accession_id}")
    assert response.status_code == 302


def test_private_experiment_collection_with_login_client(
    private_experiment_collection: ExperimentCollection, login_client: SearchClient
):
    response = login_client.get(f"/search/experiment_collection/{private_experiment_collection.accession_id}")
    assert response.status_code == 403


def test_private_experiment_collection_with_private_login_client(
    private_experiment_collection: ExperimentCollection, login_client: SearchClient
):
    login_client.add_user_experiment_collection(private_experiment_collection.accession_id)

    response = login_client.get(f"/search/experiment_collection/{private_experiment_collection.accession_id}")
    assert response.status_code == 200


def test_private_experiment_collection_with_private_login_client_no_experiments(
    private_experiment_collection: ExperimentCollection, login_client: SearchClient
):
    login_client.add_user_experiment_collection(private_experiment_collection.accession_id)

    response = login_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}?accept=application/json"
    )

    json = response.json()
    assert len(json["experiments"]) == 0


def test_private_experiment_collection_with_private_login_client_experiments(
    private_experiment_collection: ExperimentCollection, login_client: SearchClient
):
    login_client.add_user_experiment_collection(private_experiment_collection.accession_id)
    login_client.set_user_experiments([expr.accession_id for expr in private_experiment_collection.experiments.all()])

    response = login_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}?accept=application/json"
    )

    json = response.json()
    assert len(json["experiments"]) == 3


def test_private_experiment_collection_with_admin_client(
    private_experiment_collection: ExperimentCollection, portal_admin_client: SearchClient
):
    response = portal_admin_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}?accept=application/json"
    )
    assert response.status_code == 200

    json = response.json()
    assert len(json["experiments"]) == 3


def test_archived_experiment_collection_with_anon_client(
    archived_experiment_collection: ExperimentCollection, client: Client
):
    response = client.get(f"/search/experiment_collection/{archived_experiment_collection.accession_id}")
    assert response.status_code == 403


def test_archived_experiment_collection_with_login_client(
    archived_experiment_collection: ExperimentCollection, login_client: SearchClient
):
    response = login_client.get(f"/search/experiment_collection/{archived_experiment_collection.accession_id}")
    assert response.status_code == 403


def test_archived_experiment_collection_with_admin_client(
    archived_experiment_collection: ExperimentCollection, portal_admin_client: SearchClient
):
    response = portal_admin_client.get(f"/search/experiment_collection/{archived_experiment_collection.accession_id}")
    assert response.status_code == 200
