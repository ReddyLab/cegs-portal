import pytest

from cegs_portal.search.models import AccessionId, AccessionType


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId("DCPEXPR00001234"), "DCPEXPR00001234"),
        (AccessionId("DCPEXPR00001234", prefix_length=3), "DCPEXPR00001234"),
        (AccessionId("DCPEXPR00001234", prefix_length=3, id_num_length=5), "DCPEXPR00001234"),
    ],
)
def test_create_id(in_id, result_id):
    assert str(in_id) == result_id


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId("DCPEXPR00001234"), "DCPEXPR00001235"),
        (AccessionId("DCPEXPR00001234", prefix_length=3), "DCPEXPR00001235"),
        (AccessionId("DCPEXPR00001234", prefix_length=3, id_num_length=5), "DCPEXPR00001235"),
        (AccessionId("DCPEXPR0000123F"), "DCPEXPR00001240"),
    ],
)
def test_incr_id(in_id, result_id):
    in_id.incr()
    assert str(in_id) == result_id


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId.start_id(AccessionType.EXPERIMENT), "DCPEXPR00000000"),
        (AccessionId.start_id(AccessionType.GENE, prefix="FOO"), "FOOGENE00000000"),
        (AccessionId.start_id(AccessionType.CAR, prefix="FOO", id_num_length=5), "FOOCAR00000"),
    ],
)
def test_start_id(in_id, result_id):
    assert str(in_id) == result_id


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId("DCPEXPR00001234"), AccessionId("DCPEXPR00001234")),
        (AccessionId("DCPEXPR00001234", prefix_length=3), AccessionId("DCPEXPR00001234")),
        (AccessionId("DCPEXPR00001234", prefix_length=3, id_num_length=5), AccessionId("DCPEXPR00001234")),
    ],
)
def test_eq_id(in_id, result_id):
    assert str(in_id) == result_id
