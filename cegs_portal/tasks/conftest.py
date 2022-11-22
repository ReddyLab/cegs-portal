import pytest

from cegs_portal.tasks.models import ThreadTask


@pytest.fixture(scope="function", autouse=True)
def execute_before_any_test(db):
    ThreadTask.objects.all().delete()
