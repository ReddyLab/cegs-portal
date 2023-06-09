import json
from time import sleep

import pytest
from django.core.serializers.json import DjangoJSONEncoder

from cegs_portal.conftest import SearchClient
from cegs_portal.tasks.decorators import as_task
from cegs_portal.tasks.models import ThreadTask

pytestmark = pytest.mark.django_db(transaction=True)


def test_create_task():
    @as_task(pass_task_id=False)
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
    @as_task(pass_task_id=True)
    def test_func(task_id):
        ThreadTask.set_description(task_id, "Test Description")

    task = test_func()

    sleep(0.2)
    task.refresh_from_db()

    assert task is not None
    assert task.description == "Test Description"
    assert not task.failed
    assert task.failed_exception is None


def test_create_task_pass_task_description():
    @as_task(pass_task_id=True, description="Test Description")
    def test_func(task_id):
        raise Exception(f"Failed Task {task_id}")

    task = test_func()

    sleep(0.2)
    task.refresh_from_db()

    assert task is not None
    assert task.description == "Test Description"
    assert task.failed
    assert task.failed_exception == f"Failed Task {task.id}"


def test_task_exception():
    @as_task(pass_task_id=False)
    def test_func():
        raise Exception("test exception")

    task = test_func()
    sleep(0.2)
    task.refresh_from_db()

    assert task is not None
    assert task.failed
    assert task.failed_exception == "test exception"


def check_thread_task_response(task, task_json):
    encoder = DjangoJSONEncoder()
    assert task_json["description"] == task.description
    assert task_json["started_at"] == encoder.default(task.started_at)
    assert task_json["ended_at"] == (None if task.ended_at is None else encoder.default(task.ended_at))
    assert task_json["is_done"] == task.is_done
    assert task_json["failed"] == task.failed
    assert task_json["failed_exception"] == task.failed_exception


def test_non_logged_in_task_json(public_client: SearchClient):
    response = public_client.get("/tasks/task/1?accept=application/json")
    assert response.status_code == 302


def test_unfinished_thread_task_html(portal_admin_client: SearchClient, unfinished_thread_task: ThreadTask):
    response = portal_admin_client.get(f"/tasks/task/{unfinished_thread_task.id}")
    assert response.status_code == 200


def test_unfinished_thread_task_json(portal_admin_client: SearchClient, unfinished_thread_task: ThreadTask):
    response = portal_admin_client.get(f"/tasks/task/{unfinished_thread_task.id}?accept=application/json")
    assert response.status_code == 200
    json_content = json.loads(response.content)

    check_thread_task_response(unfinished_thread_task, json_content)


def test_finished_thread_task_html(portal_admin_client: SearchClient, finished_thread_task: ThreadTask):
    response = portal_admin_client.get(f"/tasks/task/{finished_thread_task.id}")
    assert response.status_code == 200


def test_finished_thread_task_json(portal_admin_client: SearchClient, finished_thread_task: ThreadTask):
    response = portal_admin_client.get(f"/tasks/task/{finished_thread_task.id}?accept=application/json")
    assert response.status_code == 200
    json_content = json.loads(response.content)

    check_thread_task_response(finished_thread_task, json_content)


def test_failed_thread_task_html(portal_admin_client: SearchClient, failed_thread_task: ThreadTask):
    response = portal_admin_client.get(f"/tasks/task/{failed_thread_task.id}")
    assert response.status_code == 200


def test_failed_thread_task_json(portal_admin_client: SearchClient, failed_thread_task: ThreadTask):
    response = portal_admin_client.get(f"/tasks/task/{failed_thread_task.id}?accept=application/json")
    assert response.status_code == 200
    json_content = json.loads(response.content)

    check_thread_task_response(failed_thread_task, json_content)


def test_non_existent_thread_task_html(portal_admin_client: SearchClient):
    response = portal_admin_client.get("/tasks/task/1")
    assert response.status_code == 404


def test_non_existent_thread_task_json(portal_admin_client: SearchClient):
    response = portal_admin_client.get("/tasks/task/1?accept=application/json")
    assert response.status_code == 404
