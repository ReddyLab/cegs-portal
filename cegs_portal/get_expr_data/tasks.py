import os
import os.path
from datetime import datetime

from django.core.files.storage import default_storage
from huey import crontab
from huey.contrib.djhuey import periodic_task

from cegs_portal.get_expr_data.models import ExperimentData, expr_data_base_path


@periodic_task(crontab(day="*/1"))
def remove_old_downloads():
    base_path = expr_data_base_path()
    _, files = default_storage.listdir(base_path)
    for file in files:
        file_path = os.path.join(base_path, file)
        file_creation_time = default_storage.get_created_time(file_path)
        created_ago = datetime.now(tz=file_creation_time.tzinfo) - file_creation_time
        if created_ago.days > 7:
            try:
                ExperimentData.objects.filter(filename=file).update(state=ExperimentData.DataState.DELETED, file="")
            except ExperimentData.DoesNotExist:
                pass
            os.remove(file_path)
