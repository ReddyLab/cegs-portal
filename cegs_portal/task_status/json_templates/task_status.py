from typing import Any, Iterable, Optional, TypedDict, Union, cast

from cegs_portal.task_status.models import TaskStatus
from cegs_portal.utils.pagination_types import Pageable, PageableJson

TaskJson = TypedDict(
    "TaskJson",
    {
        "id": str,
        "status": str,
        "description": str,
        "error_message": Optional[str],
        "created": str,
        "modified": str,
    },
)


def task_statuses(
    task_objs: Pageable[TaskStatus] | Iterable[TaskStatus], options: Optional[dict[str, Any]] = None
) -> Union[PageableJson, list[TaskJson]]:
    if options is not None and options.get("paginate"):
        task_objs = cast(Pageable[TaskStatus], task_objs)
        return {
            "object_list": [task(a, options) for a in task_objs.object_list],
            "page": task_objs.number,
            "has_next_page": task_objs.has_next(),
            "has_prev_page": task_objs.has_previous(),
            "num_pages": task_objs.paginator.num_pages,
        }
    else:
        task_objs = cast(Iterable[TaskStatus], task_objs)
        return [task(a, options) for a in task_objs]


def task(task_obj: TaskStatus, options: Optional[dict[str, Any]] = None) -> TaskJson:
    result = {
        "id": task_obj.id,
        "status": task_obj.status,
        "description": task_obj.description,
        "error_message": task_obj.error_message,
        "created": task_obj.created.isoformat(),
        "modified": task_obj.modified.isoformat(),
    }
    return cast(TaskJson, result)
