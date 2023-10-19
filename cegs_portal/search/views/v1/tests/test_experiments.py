import pytest
from django.test import Client

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import Experiment

pytestmark = pytest.mark.django_db


def test_experiments(client: Client):
    response = client.get("/search/experiments")

    # Maybe a 404 isn't quite the right
    assert response.status_code == 400


def test_experiment_list_with_anonymous_client(access_control_experiments, client: Client):
    public, private, archived = access_control_experiments
    response = client.get(f"/search/experiments?exp={public.accession_id}")
    assert response.status_code == 200

    response = client.get(f"/search/experiments?exp={private.accession_id}")
    assert response.status_code == 302  # Redirect to login

    response = client.get(f"/search/experiments?exp={archived.accession_id}")
    assert response.status_code == 403


def test_experiment_list_with_authenticated_client(access_control_experiments, login_client: SearchClient):
    public, private, archived = access_control_experiments
    response = login_client.get(f"/search/experiments?exp={public.accession_id}")
    assert response.status_code == 200

    response = login_client.get(f"/search/experiments?exp={private.accession_id}")
    assert response.status_code == 403

    response = login_client.get(f"/search/experiments?exp={archived.accession_id}")
    assert response.status_code == 403


def test_experiment_list_with_authenticated_authorized_client(
    login_client: SearchClient, access_control_experiments: tuple[Experiment, Experiment, Experiment]
):
    public, private, archived = access_control_experiments

    login_client.set_user_experiments([private.accession_id, archived.accession_id])
    response = login_client.get(f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}")
    assert response.status_code == 200

    login_client.set_user_experiments([private.accession_id, archived.accession_id])
    response = login_client.get(
        f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}&exp={archived.accession_id}"
    )
    assert response.status_code == 403


def test_experiment_list_with_authenticated_authorized_group_client(
    group_login_client: Client, access_control_experiments: tuple[Experiment, Experiment, Experiment]
):
    public, private, archived = access_control_experiments

    group_login_client.set_group_experiments([private.accession_id, archived.accession_id])
    response = group_login_client.get(f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}")
    assert response.status_code == 200

    group_login_client.set_user_experiments([private.accession_id, archived.accession_id])
    response = group_login_client.get(
        f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}&exp={archived.accession_id}"
    )
    assert response.status_code == 403
