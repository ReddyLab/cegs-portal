import pytest
from django.core.exceptions import BadRequest
from django.test import Client
from pytest import MonkeyPatch

import cegs_portal.search.views.v1.experiment_coverage as exp_cov
from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.models import Experiment

pytestmark = pytest.mark.django_db


@pytest.fixture
def view():
    return exp_cov.ExperimentCoverageView.as_view()


def mock_coverage_path(acc_id, chrom):
    if chrom is None:
        return "level1.ecd"
    else:
        return f"level2_{chrom}.ecd"


def filter_nothing(zoom_chr=None):
    return [
        [],  # categorical filter values
        [[-5, 5], [0.0, 1.0]],  # effect size, significance numeric filter values
    ]


def filter_everything():
    return [
        [],  # categorical filter values
        [[10, 11], [2.0, 3.0]],  # effect size, significance numeric filter values
    ]


def test_coverage_e2e(client: Client, monkeypatch: MonkeyPatch, experiment: Experiment):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    response = client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}/{experiment.default_analysis.accession_id}&accept=application/json",
        {"filters": filter_nothing()},
        content_type="application/json",
    )

    assert response.status_code == 200

    response = client.post(
        "/search/experiment_coverage?accept=application/json",
        {"filters": filter_nothing()},
        content_type="application/json",
    )

    assert response.status_code == 400


def test_coverage_filter_nothing_json(
    public_test_client: RequestBuilder, experiment: Experiment, view, monkeypatch: MonkeyPatch
):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    response = public_test_client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}/{experiment.default_analysis.accession_id}&accept=application/json",
        {"filters": filter_nothing()},
        content_type="application/json",
    ).request(view)

    filtered_data = response.json()

    assert len(filtered_data["chromosomes"][0]["target_intervals"]) > 0
    assert len(filtered_data["chromosomes"][0]["source_intervals"]) > 0

    assert response.status_code == 200


def test_coverage_filter_nothing_zoom_json(
    public_test_client: RequestBuilder, experiment: Experiment, view, monkeypatch: MonkeyPatch
):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    response = public_test_client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}/{experiment.default_analysis.accession_id}&accept=application/json",
        {"filters": filter_nothing(), "zoom": "1"},
        content_type="application/json",
    ).request(view)

    filtered_data = response.json()

    assert len(filtered_data["chromosomes"][0]["target_intervals"]) > 0
    assert len(filtered_data["chromosomes"][0]["source_intervals"]) > 0

    assert response.status_code == 200


def test_coverage_filter_everything_json(
    public_test_client: RequestBuilder, experiment: Experiment, view, monkeypatch: MonkeyPatch
):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    response = public_test_client.post(
        f"/search/experiment_coverage?exp={experiment.accession_id}/{experiment.default_analysis.accession_id}&accept=application/json",
        {"filters": filter_everything()},
        content_type="application/json",
    ).request(view)

    filtered_data = response.json()

    assert len(filtered_data["chromosomes"][0]["target_intervals"]) == 0
    assert len(filtered_data["chromosomes"][0]["source_intervals"]) == 0
    assert response.status_code == 200


@pytest.mark.usefixtures("experiment")
def test_coverage_no_experiment_json(public_test_client: RequestBuilder, view, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    with pytest.raises(BadRequest):
        public_test_client.post(
            "/search/experiment_coverage?accept=application/json",
            {"filters": filter_everything(), "zoom": "1"},
            content_type="application/json",
        ).request(view)


def test_coverage_no_filter_json(
    public_test_client: RequestBuilder, experiment: Experiment, view, monkeypatch: MonkeyPatch
):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    with pytest.raises(BadRequest):
        public_test_client.post(
            f"/search/experiment_coverage?exp={experiment.accession_id}/{experiment.default_analysis.accession_id}&accept=application/json",
            {"zoom": "1"},
            content_type="application/json",
        ).request(view)


def test_coverage_invalid_zoom_chrom_json(
    public_test_client: RequestBuilder, experiment: Experiment, view, monkeypatch: MonkeyPatch
):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    with pytest.raises(BadRequest):
        public_test_client.post(
            f"/search/experiment_coverage?exp={experiment.accession_id}/{experiment.default_analysis.accession_id}&accept=application/json",
            {"filters": filter_nothing(), "zoom": "Q"},
            content_type="application/json",
        ).request(view)


def test_coverage_bad_zoom_chrom_json(
    public_test_client: RequestBuilder, experiment: Experiment, view, monkeypatch: MonkeyPatch
):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    with pytest.raises(BadRequest):
        public_test_client.post(
            f"/search/experiment_coverage?exp={experiment.accession_id}/{experiment.default_analysis.accession_id}&accept=application/json",
            {"filters": filter_nothing(), "zoom": "5"},
            content_type="application/json",
        ).request(view)


def test_coverage_html(public_test_client: RequestBuilder, experiment: Experiment, view, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(exp_cov, "coverage_path", mock_coverage_path)
    with pytest.raises(BadRequest):
        public_test_client.post(
            f"/search/experiment_coverage?exp={experiment.accession_id}",
            {"filters": filter_nothing(), "chromosomes": ["chr1"]},
            content_type="application/json",
        ).request(view)
