import pytest
from django.core.exceptions import BadRequest, PermissionDenied
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.views.v1.experiment import ExperimentsView

pytestmark = pytest.mark.django_db


@pytest.fixture
def experiments_view():
    return ExperimentsView.as_view()


def test_experiments(public_test_client: RequestBuilder, experiments_view):
    with pytest.raises(BadRequest):
        public_test_client.get("/search/experiments").request(experiments_view)


def test_experiment_list_with_anonymous_client_e2e(access_control_experiments, client: Client):
    public, private, archived = access_control_experiments
    response = client.get(f"/search/experiments?exp={public.accession_id}")
    assert response.status_code == 200

    response = client.get(f"/search/experiments?exp={private.accession_id}")
    assert response.status_code == 302  # Redirect to login

    response = client.get(f"/search/experiments?exp={archived.accession_id}")
    assert response.status_code == 403


def test_experiment_list_with_anonymous_client(
    public_test_client: RequestBuilder, experiments_view, access_control_experiments
):
    public, private, archived = access_control_experiments
    response = public_test_client.get(f"/search/experiments?exp={public.accession_id}").request(experiments_view)
    assert response.status_code == 200

    response = public_test_client.get(f"/search/experiments?exp={private.accession_id}").request(experiments_view)
    assert response.status_code == 302  # Redirect to login

    with pytest.raises(PermissionDenied):
        public_test_client.get(f"/search/experiments?exp={archived.accession_id}").request(experiments_view)


def test_experiment_list_with_authenticated_client(
    login_test_client: RequestBuilder, experiments_view, access_control_experiments
):
    public, private, archived = access_control_experiments
    response = login_test_client.get(f"/search/experiments?exp={public.accession_id}").request(experiments_view)
    assert response.status_code == 200

    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/experiments?exp={private.accession_id}").request(experiments_view)

    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/experiments?exp={archived.accession_id}").request(experiments_view)


def test_experiment_list_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, experiments_view, access_control_experiments
):
    public, private, archived = access_control_experiments

    login_test_client.set_user_experiments([private.accession_id, archived.accession_id])

    response = login_test_client.get(
        f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}"
    ).request(experiments_view)
    assert response.status_code == 200

    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}&exp={archived.accession_id}"
        ).request(experiments_view)


def test_experiment_list_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, experiments_view, access_control_experiments
):
    public, private, archived = access_control_experiments

    group_login_test_client.set_group_experiments([private.accession_id, archived.accession_id])

    response = group_login_test_client.get(
        f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}"
    ).request(experiments_view)
    assert response.status_code == 200

    with pytest.raises(PermissionDenied):
        group_login_test_client.get(
            f"/search/experiments?exp={public.accession_id}&exp={private.accession_id}&exp={archived.accession_id}"
        ).request(experiments_view)
