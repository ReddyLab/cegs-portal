from cegs_portal.task_status.models import TaskStatus


def get_status(task_id):
    try:
        task = TaskStatus.objects.get(id=task_id)
    except TaskStatus.DoesNotExist:
        task = None
    return task
