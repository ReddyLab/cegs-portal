import pytest

from cegs_portal.search.models import AccessionId, AccessionType


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId("DCPEXPR0000001234"), "DCPEXPR0000001234"),
        (AccessionId("DCPEXPR0000001234", prefix_length=3), "DCPEXPR0000001234"),
        (AccessionId("DCPEXPR0000001234", prefix_length=3, id_num_length=5), "DCPEXPR0000001234"),
    ],
)
def test_create_id(in_id, result_id):
    assert str(in_id) == result_id


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId("DCPEXPR0000001234"), "DCPEXPR0000001235"),
        (AccessionId("DCPEXPR0000001234", prefix_length=3), "DCPEXPR0000001235"),
        (AccessionId("DCPEXPR0000001234", prefix_length=3, id_num_length=5), "DCPEXPR0000001235"),
        (AccessionId("DCPEXPR000000123F"), "DCPEXPR0000001240"),
    ],
)
def test_incr_id(in_id, result_id):
    in_id.incr()
    assert str(in_id) == result_id


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId.start_id(AccessionType.EXPERIMENT), "DCPEXPR0000000000"),
        (AccessionId.start_id(AccessionType.GENE, prefix="FOO"), "FOOGENE0000000000"),
        (AccessionId.start_id(AccessionType.CAR, prefix="FOO", id_num_length=5), "FOOCAR00000"),
    ],
)
def test_start_id(in_id, result_id):
    assert str(in_id) == result_id


@pytest.mark.parametrize(
    "in_id, result_id",
    [
        (AccessionId("DCPEXPR0000001234"), AccessionId("DCPEXPR0000001234")),
        (AccessionId("DCPEXPR0000001234", prefix_length=3), AccessionId("DCPEXPR0000001234")),
        (AccessionId("DCPEXPR0000001234", prefix_length=3, id_num_length=5), AccessionId("DCPEXPR0000001234")),
    ],
)
def test_eq_id(in_id, result_id):
    assert str(in_id) == result_id
