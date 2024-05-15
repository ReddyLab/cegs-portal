import pytest

from cegs_portal.task_status.factories import TaskStatusFactory


@pytest.fixture
def task():
    return TaskStatusFactory()
