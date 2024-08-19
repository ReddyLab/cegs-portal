import pytest

from cegs_portal.search.models import ChromosomeLocation
from cegs_portal.search.view_models.v1.search import Search
from cegs_portal.users.models import UserType

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("reg_effects")
def test_sig_reo_loc_search():
    result = Search.sig_reo_loc_search(ChromosomeLocation("chr1", "1", "1000000"))

    assert len(result) == 1
    assert len(result[0][1]) == 1


def test_private_sig_reo_loc_search(private_reg_effects):
    _, _, _, _, _, experiment = private_reg_effects
    result = Search.sig_reo_loc_search(ChromosomeLocation("chr1", "1", "1000000"))

    assert len(result) == 0

    result = Search.sig_reo_loc_search(
        ChromosomeLocation("chr1", "1", "1000000"), private_experiments=[experiment.accession_id]
    )

    assert len(result) == 1
    assert len(result[0][1]) == 1


@pytest.mark.usefixtures("reg_effects")
def test_feature_sig_reos():
    result = Search.feature_sig_reos(ChromosomeLocation("chr1", "1", "1000000"), "hg38", [])
    assert len(result) == 1


def test_private_feature_sig_reos(private_reg_effects):
    _, _, _, _, _, experiment = private_reg_effects

    result = Search.feature_sig_reos(ChromosomeLocation("chr1", "1", "1000000"), "hg38", [])
    assert len(result) == 0

    result = Search.feature_sig_reos(
        ChromosomeLocation("chr1", "1", "1000000"),
        "hg38",
        [],
        user_type=UserType.LOGGED_IN,
        private_experiments=[experiment.accession_id],
    )
    assert len(result) == 1


@pytest.mark.usefixtures("private_reg_effects")
def test_admin_feature_sig_reos():
    result = Search.feature_sig_reos(ChromosomeLocation("chr1", "1", "1000000"), "hg38", [])
    assert len(result) == 0

    result = Search.feature_sig_reos(ChromosomeLocation("chr1", "1", "1000000"), "hg38", [], user_type=UserType.ADMIN)
    assert len(result) == 1
