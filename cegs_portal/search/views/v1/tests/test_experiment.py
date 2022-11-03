import json

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
