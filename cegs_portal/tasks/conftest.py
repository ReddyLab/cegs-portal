import pytest

from cegs_portal.search.conftest import (  # noqa: F401 used as fixtures in test_tasks.py
    login_client,
    public_client,
)
from cegs_portal.tasks.factories import ThreadTaskFactory
from cegs_portal.tasks.models import ThreadTask


@pytest.fixture(scope="function", autouse=True)
def execute_before_any_test(db):
    ThreadTask.objects.all().delete()


@pytest.fixture
def unfinished_thread_task() -> ThreadTask:
    return ThreadTaskFactory(ended_at=None, is_done=False)


@pytest.fixture
def finished_thread_task() -> ThreadTask:
    return ThreadTaskFactory()


@pytest.fixture
def failed_thread_task() -> ThreadTask:
    return ThreadTaskFactory(failed=True, failed_exception="task failed")
