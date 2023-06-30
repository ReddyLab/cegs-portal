def task(task_obj, options):
    return {
        "description": task_obj.description,
        "started_at": task_obj.started_at,
        "ended_at": task_obj.ended_at,
        "is_done": task_obj.is_done,
        "failed": task_obj.failed,
        "failed_exception": task_obj.failed_exception,
    }
