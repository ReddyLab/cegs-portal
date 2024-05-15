import json

import pytest

from cegs_portal.conftest import SearchClient
from cegs_portal.task_status.decorators import handle_error
from cegs_portal.task_status.json_templates.task_status import task_statuses
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


def test_task_status_json(task: TaskStatus):
    assert task_statuses([task]) == [
        {
            "id": task.id,
            "status": task.status,
            "description": task.description,
            "error_message": None,
            "created": task.created.isoformat(),
            "modified": task.modified.isoformat(),
        }
    ]


def test_task_list_view(task: TaskStatus, login_client: SearchClient):
    task.user = login_client.user
    task.save()

    response = login_client.get(f"/task_status/{login_client.username}?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert json_content == {
        "object_list": [
            {
                "id": str(task.id),
                "status": task.status,
                "description": task.description,
                "error_message": None,
                "created": task.created.isoformat(),
                "modified": task.modified.isoformat(),
            }
        ],
        "page": 1,
        "has_next_page": False,
        "has_prev_page": False,
        "num_pages": 1,
    }


def test_no_task_list_view(task: TaskStatus, login_client: SearchClient):
    response = login_client.get(f"/task_status/{login_client.username}?accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert json_content == {
        "object_list": [],
        "page": 1,
        "has_next_page": False,
        "has_prev_page": False,
        "num_pages": 1,
    }
