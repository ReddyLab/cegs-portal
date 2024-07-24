import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from cegs_portal.conftest import RequestBuilder, SearchClient
from cegs_portal.search.models import ExperimentCollection
from cegs_portal.search.views.v1.experiment_collection import ExperimentCollectionView

pytestmark = pytest.mark.django_db


@pytest.fixture
def view():
    return ExperimentCollectionView.as_view()


def check_experiment_collection(collection: ExperimentCollection, response_json):
    assert collection.accession_id == response_json["accession_id"]
    assert collection.name == response_json["name"]
    assert collection.description == response_json["description"]


def test_experiment_collection_with_public_client(
    experiment_collection: ExperimentCollection, view, public_test_client: RequestBuilder
):
    response = public_test_client.get(f"/search/experiment_collection/{experiment_collection.accession_id}").request(
        view, expcol_id=experiment_collection.accession_id
    )
    assert response.status_code == 200

    response = public_test_client.get(
        f"/search/experiment_collection/{experiment_collection.accession_id}?accept=application/json",
    ).request(view, expcol_id=experiment_collection.accession_id)
    assert response.status_code == 200

    check_experiment_collection(experiment_collection, response.json())


def test_experiment_collection_with_public_client_e2e(
    experiment_collection: ExperimentCollection, public_client: SearchClient
):
    response = public_client.get(f"/search/experiment_collection/{experiment_collection.accession_id}")
    assert response.status_code == 200

    response = public_client.get(
        f"/search/experiment_collection/{experiment_collection.accession_id}?accept=application/json",
    )
    assert response.status_code == 200

    check_experiment_collection(experiment_collection, response.json())

    response = public_client.get("/search/experiment_collection/DCPEXCLFFFFFFFFFF")
    assert response.status_code == 404

    response = public_client.get("/search/experiment_collection/lkasjdfjsdf")
    assert response.status_code == 404


def test_fake_experiment_collection_with_anonymous_client(view, public_test_client: RequestBuilder):
    faux_id = "DCPEXCLFFFFFFFFFF"

    with pytest.raises(Http404):
        public_test_client.get(f"/search/experiment_collection/{faux_id}").request(view, expcol_id=faux_id)


def test_private_experiment_collection_with_anonymous_client(
    private_experiment_collection: ExperimentCollection, view, public_test_client: RequestBuilder
):
    response = public_test_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}"
    ).request(view, expcol_id=private_experiment_collection.accession_id)
    assert response.status_code == 302


def test_private_experiment_collection_with_login_client(
    private_experiment_collection: ExperimentCollection, view, login_test_client: RequestBuilder
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/experiment_collection/{private_experiment_collection.accession_id}").request(
            view, expcol_id=private_experiment_collection.accession_id
        )


def test_private_experiment_collection_with_private_login_client(
    private_experiment_collection: ExperimentCollection, view, login_test_client: RequestBuilder
):
    login_test_client.add_user_experiment_collection(private_experiment_collection.accession_id)

    response = login_test_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}"
    ).request(view, expcol_id=private_experiment_collection.accession_id)
    assert response.status_code == 200


def test_private_experiment_collection_with_private_login_client_no_experiments(
    private_experiment_collection: ExperimentCollection, view, login_test_client: RequestBuilder
):
    login_test_client.add_user_experiment_collection(private_experiment_collection.accession_id)

    response = login_test_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}?accept=application/json"
    ).request(view, expcol_id=private_experiment_collection.accession_id)

    assert len(response.json()["experiments"]) == 0


def test_private_experiment_collection_with_private_login_client_experiments(
    private_experiment_collection: ExperimentCollection, view, login_test_client: RequestBuilder
):
    login_test_client.add_user_experiment_collection(private_experiment_collection.accession_id)
    login_test_client.set_user_experiments(
        [expr.accession_id for expr in private_experiment_collection.experiments.all()]
    )

    response = login_test_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}?accept=application/json"
    ).request(view, expcol_id=private_experiment_collection.accession_id)

    assert len(response.json()["experiments"]) == 3


def test_private_experiment_collection_with_admin_client(
    private_experiment_collection: ExperimentCollection, view, portal_admin_test_client: RequestBuilder
):
    response = portal_admin_test_client.get(
        f"/search/experiment_collection/{private_experiment_collection.accession_id}?accept=application/json"
    ).request(view, expcol_id=private_experiment_collection.accession_id)
    assert response.status_code == 200

    assert len(response.json()["experiments"]) == 3


def test_archived_experiment_collection_with_anon_client(
    archived_experiment_collection: ExperimentCollection, view, public_test_client: RequestBuilder
):
    with pytest.raises(PermissionDenied):
        public_test_client.get(f"/search/experiment_collection/{archived_experiment_collection.accession_id}").request(
            view, expcol_id=archived_experiment_collection.accession_id
        )


def test_archived_experiment_collection_with_login_client(
    archived_experiment_collection: ExperimentCollection, view, login_test_client: RequestBuilder
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/experiment_collection/{archived_experiment_collection.accession_id}").request(
            view, expcol_id=archived_experiment_collection.accession_id
        )


def test_archived_experiment_collection_with_admin_client(
    archived_experiment_collection: ExperimentCollection, view, portal_admin_test_client: RequestBuilder
):
    response = portal_admin_test_client.get(
        f"/search/experiment_collection/{archived_experiment_collection.accession_id}"
    ).request(view, expcol_id=archived_experiment_collection.accession_id)
    assert response.status_code == 200
