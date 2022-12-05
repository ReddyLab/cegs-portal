from time import sleep

import pytest

from cegs_portal.tasks.decorators import as_task
from cegs_portal.tasks.models import ThreadTask

pytestmark = pytest.mark.django_db


def test_create_task():
    @as_task(pass_id=False)
    def test_func():
        pass

    all_tasks = ThreadTask.objects.all()

    assert all_tasks.count() == 0

    test_func()
    sleep(0.2)

    assert all_tasks.count() == 1
    assert all_tasks.first().description is None
    assert not all_tasks.first().failed
    assert all_tasks.first().failed_exception is None


def test_create_task_description():
    @as_task(description="Test Description")
    def test_func():
        pass

    all_tasks = ThreadTask.objects.all()

    assert all_tasks.count() == 0

    test_func()
    sleep(0.2)

    assert all_tasks.count() == 1
    assert all_tasks.first().description == "Test Description"
    assert not all_tasks.first().failed


def test_create_task_pass_id_description():
    @as_task(pass_id=True, description="Test Description")
    def test_func(task_id):
        raise Exception(f"Failed Task {task_id}")

    all_tasks = ThreadTask.objects.all()

    assert all_tasks.count() == 0

    test_func()
    sleep(0.2)

    assert all_tasks.count() == 1
    first_task = all_tasks.first()
    assert first_task.description == "Test Description"
    assert first_task.failed
    assert first_task.failed_exception == f"Failed Task {first_task.id}"


def test_task_exception():
    @as_task(pass_id=False)
    def test_func():
        raise Exception("test exception")

    all_tasks = ThreadTask.objects.all()

    assert all_tasks.count() == 0

    test_func()
    sleep(0.2)

    assert all_tasks.count() == 1
    first_task = all_tasks.first()
    assert first_task.failed
    assert first_task.failed_exception == "test exception"
