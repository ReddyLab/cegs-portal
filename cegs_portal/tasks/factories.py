from datetime import datetime, timedelta, timezone

from factory import Faker
from factory.django import DjangoModelFactory

from cegs_portal.tasks.models import ThreadTask


class ThreadTaskFactory(DjangoModelFactory):
    class Meta:
        model = ThreadTask

    description = Faker("text", max_nb_chars=140)
    started_at = datetime.now(timezone.utc)
    ended_at = datetime.now(timezone.utc) + timedelta(seconds=20)
    is_done = True
    failed = False
    failed_exception = None
