from time import sleep

import pytest

from cegs_portal.tasks.decorators import as_task

pytestmark = pytest.mark.django_db(transaction=True)


def test_create_task():
    @as_task(pass_task=False)
    def test_func():
        pass

    task = test_func()
    sleep(0.2)

    assert task is not None
    assert task.description is None
    assert not task.failed
    assert task.failed_exception is None


def test_create_task_description():
    @as_task(description="Test Description")
    def test_func():
        pass

    task = test_func()
    sleep(0.2)

    assert task is not None
    assert task.description == "Test Description"
    assert not task.failed


def test_create_task_pass_task():
    @as_task(pass_task=True)
    def test_func(task):
        task.set_description("Test Description")

    task = test_func()

    sleep(0.2)
    task.refresh_from_db()

    assert task is not None
    assert task.description == "Test Description"
    assert not task.failed
    assert task.failed_exception is None


def test_create_task_pass_task_description():
    @as_task(pass_task=True, description="Test Description")
    def test_func(task):
        raise Exception(f"Failed Task {task.id}")

    task = test_func()

    sleep(0.2)
    task.refresh_from_db()

    assert task is not None
    assert task.description == "Test Description"
    assert task.failed
    assert task.failed_exception == f"Failed Task {task.id}"


def test_task_exception():
    @as_task(pass_task=False)
    def test_func():
        raise Exception("test exception")

    task = test_func()
    sleep(0.2)
    task.refresh_from_db()

    assert task is not None
    assert task.failed
    assert task.failed_exception == "test exception"
