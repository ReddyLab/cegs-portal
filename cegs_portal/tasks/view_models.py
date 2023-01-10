from cegs_portal.tasks.models import ThreadTask


class ThreadTaskSearch:
    @classmethod
    def id_search(cls, task_id):
        return ThreadTask.objects.get(id=task_id)
