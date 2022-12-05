import json
import os

import pytest
from django.test import Client
from exp_viz import load_coverage_data_allow_threads
from pytest import MonkeyPatch

import cegs_portal.search.views.v1.experiment_coverage as exp_cov
from cegs_portal.search.models import Experiment

pytestmark = pytest.mark.django_db


def mock_load_coverage(exp_acc_id, chrom):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return load_coverage_data_allow_threads(os.path.join(current_dir, "level2_1.bin"))


def filter_nothing(zoom_chr=None):
    return [
        [],  # discrete filter values
        [[-5, 5], [0.0, 1.0]],  # effect size, significance continuous filter values
    ]


def filter_everything():
    return [
        [],  # discrete filter values
        [[10, 11], [2.0, 3.0]],  # effect size, significance continuous filter values
    ]


def test_coverage_filter_nothing_json(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}&accept=application/json",
        {"filters": filter_nothing(), "chromosomes": ["chr1"]},
        content_type="application/json",
    )

    filtered_data = json.loads(response.content)

    assert len(filtered_data["chromosomes"][0]["target_intervals"]) > 0
    assert len(filtered_data["chromosomes"][0]["source_intervals"]) > 0

    assert response.status_code == 200


def test_coverage_filter_everything_json(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}&accept=application/json",
        {"filters": filter_everything(), "chromosomes": ["chr1"]},
        content_type="application/json",
    )

    filtered_data = json.loads(response.content)

    assert len(filtered_data["chromosomes"][0]["target_intervals"]) == 0
    assert len(filtered_data["chromosomes"][0]["source_intervals"]) == 0
    assert response.status_code == 200


def test_coverage_no_experiment_json(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        "/search/experiment_coverage?accept=application/json",
        {"filters": filter_everything(), "chromosomes": ["chr1"], "zoom": "Q"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_coverage_no_filter_json(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}&accept=application/json",
        {"chromosomes": ["chr1"], "zoom": "Q"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_coverage_no_chroms_json(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}&accept=application/json",
        {"filters": filter_nothing(), "zoom": "Q"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_coverage_bad_chrom_json(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}&accept=application/json",
        {"filters": filter_nothing(), "chromosomes": ["chr1"], "zoom": "Q"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_coverage_wrong_chrom_json(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    # TODO: I'm not sure what should happen here, so we'll skip the test for now. But there should
    #  be a test!
    return

    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}&accept=application/json",
        {"filters": filter_nothing(), "chromosomes": ["chr2"]},
        content_type="application/json",
    )

    filtered_data = json.loads(response.content)

    assert len(filtered_data["chromosomes"][0]["target_intervals"]) == 0
    assert len(filtered_data["chromosomes"][0]["source_intervals"]) == 0
    assert response.status_code == 200


def test_coverage_html(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "load_coverage", mock_load_coverage)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}",
        {"filters": filter_nothing(), "chromosomes": ["chr1"]},
        content_type="application/json",
    )

    assert response.status_code == 400
