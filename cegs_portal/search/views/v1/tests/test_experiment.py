import json

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.models import Experiment
from cegs_portal.search.views.v1.experiment import ExperimentView

pytestmark = pytest.mark.django_db


@pytest.fixture
def experiment_view():
    return ExperimentView.as_view()


def test_experiment_e2e(client: Client, experiment: Experiment):
    response = client.get(f"/search/experiment/{experiment.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["accession_id"] == experiment.accession_id
    assert json_content["name"] == experiment.name
    assert json_content["description"] == (experiment.description if experiment.description is not None else "")

    response = client.get(f"/search/experiment/{experiment.accession_id}")

    assert response.status_code == 200

    response = client.get("/search/experiment/DCPEXPRFFFFFFFFFF?accept=application/json")

    assert response.status_code == 404


def test_experiment_json(public_test_client: RequestBuilder, experiment_view, experiment: Experiment):
    response = public_test_client.get(f"/search/experiment/{experiment.accession_id}?accept=application/json").request(
        experiment_view, exp_id=experiment.accession_id
    )

    assert response.status_code == 200
    json_content = response.json()

    assert json_content["accession_id"] == experiment.accession_id
    assert json_content["name"] == experiment.name
    assert json_content["description"] == (experiment.description if experiment.description is not None else "")


def test_experiment_html(public_test_client: RequestBuilder, experiment_view, experiment: Experiment):
    response = public_test_client.get(f"/search/experiment/{experiment.accession_id}").request(
        experiment_view, exp_id=experiment.accession_id
    )

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_no_experiment_html(public_test_client: RequestBuilder, experiment_view):
    with pytest.raises(Http404):
        public_test_client.get("/search/experiment/DCPEXPR0000000000").request(
            experiment_view, exp_id="DCPEXPR0000000000"
        )


def test_experiment_with_anonymous_client(
    public_test_client: RequestBuilder, experiment_view, private_experiment: Experiment
):
    response = public_test_client.get(
        f"/search/experiment/{private_experiment.accession_id}?accept=application/json"
    ).request(experiment_view, exp_id=private_experiment.accession_id)
    assert response.status_code == 302


def test_experiment_with_authenticated_client(
    login_test_client: RequestBuilder, experiment_view, private_experiment: Experiment
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/experiment/{private_experiment.accession_id}?accept=application/json").request(
            experiment_view, exp_id=private_experiment.accession_id
        )


def test_experiment_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, experiment_view, private_experiment: Experiment
):
    login_test_client.set_user_experiments([private_experiment.accession_id])
    response = login_test_client.get(
        f"/search/experiment/{private_experiment.accession_id}?accept=application/json"
    ).request(experiment_view, exp_id=private_experiment.accession_id)
    assert response.status_code == 200


def test_experiment_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, experiment_view, private_experiment: Experiment
):
    group_login_test_client.set_group_experiments([private_experiment.accession_id])
    response = group_login_test_client.get(
        f"/search/experiment/{private_experiment.accession_id}?accept=application/json"
    ).request(experiment_view, exp_id=private_experiment.accession_id)
    assert response.status_code == 200


def test_archived_experiment_with_anonymous_client(
    public_test_client: RequestBuilder, experiment_view, archived_experiment: Experiment
):
    with pytest.raises(PermissionDenied):
        public_test_client.get(
            f"/search/experiment/{archived_experiment.accession_id}?accept=application/json"
        ).request(experiment_view, exp_id=archived_experiment.accession_id)


def test_archived_experiment_with_authenticated_client(
    login_test_client: RequestBuilder, experiment_view, archived_experiment: Experiment
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json").request(
            experiment_view, exp_id=archived_experiment.accession_id
        )


def test_archived_experiment_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, experiment_view, archived_experiment: Experiment
):
    login_test_client.set_user_experiments([archived_experiment.accession_id])
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/experiment/{archived_experiment.accession_id}?accept=application/json").request(
            experiment_view, exp_id=archived_experiment.accession_id
        )


def test_archived_experiment_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, experiment_view, archived_experiment: Experiment
):
    group_login_test_client.set_group_experiments([archived_experiment.accession_id])
    with pytest.raises(PermissionDenied):
        group_login_test_client.get(
            f"/search/experiment/{archived_experiment.accession_id}?accept=application/json"
        ).request(experiment_view, exp_id=archived_experiment.accession_id)
