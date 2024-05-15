import pytest

from cegs_portal.task_status.decorators import handle_error
from cegs_portal.task_status.models import TaskStatus

pytestmark = pytest.mark.django_db


def test_task_status_waiting(task: TaskStatus):
    assert task.status == TaskStatus.TaskState.WAITING


def test_task_status_started(task: TaskStatus):
    task.start()
    assert task.status == TaskStatus.TaskState.STARTED


def test_task_status_finished(task: TaskStatus):
    task.finish()
    assert task.status == TaskStatus.TaskState.FINISHED


def test_task_status_error(task: TaskStatus):
    task.error("Problem")
    assert task.status == TaskStatus.TaskState.ERROR


def test_task_status_handle_error(task: TaskStatus):
    def error_function():
        raise ValueError("Bad Value")

    f = handle_error(error_function, task)
    with pytest.raises(ValueError):
        f()

    assert task.status == TaskStatus.TaskState.ERROR
    assert task.error_message == "Bad Value"
