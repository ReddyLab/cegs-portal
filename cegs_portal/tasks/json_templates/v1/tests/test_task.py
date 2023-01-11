import pytest

from cegs_portal.tasks.json_templates.v1.task import task
from cegs_portal.tasks.models import ThreadTask

pytestmark = pytest.mark.django_db


def check_thread_task_object(task, task_dict):
    assert task_dict["description"] == task.description
    assert task_dict["started_at"] == task.started_at
    assert task_dict["ended_at"] == task.ended_at
    assert task_dict["is_done"] == task.is_done
    assert task_dict["failed"] == task.failed
    assert task_dict["failed_exception"] == task.failed_exception


def test_unfinished_thread_task(unfinished_thread_task: ThreadTask):
    check_thread_task_object(unfinished_thread_task, task(unfinished_thread_task, {}))


def test_finished_thread_task(finished_thread_task: ThreadTask):
    check_thread_task_object(finished_thread_task, task(finished_thread_task, {}))


def test_failed_thread_task(failed_thread_task: ThreadTask):
    check_thread_task_object(failed_thread_task, task(failed_thread_task, {}))
