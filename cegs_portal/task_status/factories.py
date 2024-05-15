from factory import Faker
from factory.django import DjangoModelFactory
from faker import Faker as F

from cegs_portal.task_status.models import TaskStatus


class TaskStatusFactory(DjangoModelFactory):
    class Meta:
        model = TaskStatus
        exclude = ("_faker", "_created_date")

    _faker = F()
    description = Faker("text", max_nb_chars=512)
    status = TaskStatus.TaskState.WAITING
    error_message = None
    _created_date = Faker("date_this_month")
    created = _created_date
    modified = Faker("date_between", start_date=_created_date)
