import pytest

from cegs_portal.get_expr_data.view_models import (
    ReoDataSource,
    retrieve_experiment_data,
)

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("reg_effects")]


def test_retrieve_both_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], ReoDataSource.BOTH
    )

    assert len(result) == 3


def test_retrieve_source_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], ReoDataSource.SOURCES
    )

    assert len(result) == 2


def test_retrieve_target_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], ReoDataSource.TARGETS
    )

    assert len(result) == 2
