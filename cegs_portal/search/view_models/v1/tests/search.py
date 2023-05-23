import pytest

from cegs_portal.search.models import ChromosomeLocation
from cegs_portal.search.view_models.v1.search import Search

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.usefixtures("reg_effects")
def test_sig_reo_loc_search():
    result = Search.sig_reo_loc_search(ChromosomeLocation("chr1", "1", "1000000"))

    assert len(result) == 2


def test_private_sig_reo_loc_search(private_reg_effects):
    _, _, _, _, _, _, experiment = private_reg_effects
    result = Search.sig_reo_loc_search(ChromosomeLocation("chr1", "1", "1000000"))

    assert len(result) == 0

    result = Search.sig_reo_loc_search(ChromosomeLocation("chr1", "1", "1000000"), [experiment.accession_id])

    assert len(result) == 2
