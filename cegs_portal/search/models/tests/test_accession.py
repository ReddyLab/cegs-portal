import pytest

from cegs_portal.search.models import (
    AccessionId,
    AccessionIdLog,
    AccessionIds,
    AccessionType,
)


@pytest.mark.django_db()
def test_accession_creation():
    with AccessionIds(message="Test") as accession_ids:
        old = accession_ids.incr(AccessionType.GENE)
        start_id = AccessionId.start_id(AccessionType.GENE)
        assert old == str(start_id)


@pytest.mark.django_db()
def test_accession_incr():
    with AccessionIds(message="Test") as accession_ids:
        accession_ids.incr(AccessionType.GENE)
        start_id = AccessionId.start_id(AccessionType.GENE)
        new = accession_ids.incr(AccessionType.GENE)
        start_id.incr()
        assert new == str(start_id)


@pytest.mark.django_db()
def test_accession_save():
    with AccessionIds(message="Test") as accession_ids:
        accession_ids.incr(AccessionType.GENE)
    log_entry = AccessionIdLog.objects.get(accession_type=AccessionType.GENE)
    assert log_entry.message == "Test"


@pytest.mark.django_db()
def test_accession_multi_save():
    with AccessionIds(message="Test") as accession_ids:
        accession_ids.incr(AccessionType.GENE)

    with AccessionIds(message="Test 2") as accession_ids:
        accession_ids.incr(AccessionType.GENE)

    log_entry = AccessionIdLog.latest(AccessionType.GENE)
    assert log_entry.message == "Test 2"


@pytest.mark.django_db()
def test_accession_latest():
    with AccessionIds(message="Test") as accession_ids:
        accession_ids.incr(AccessionType.GENE)

    with AccessionIds(message="Test 2") as accession_ids:
        accession_ids.incr(AccessionType.GENE)

    log_entry1 = AccessionIdLog.latest(AccessionType.GENE)
    log_entry2 = AccessionIdLog.objects.filter(accession_type=AccessionType.GENE).order_by("-created_at").first()
    assert log_entry1 == log_entry2
