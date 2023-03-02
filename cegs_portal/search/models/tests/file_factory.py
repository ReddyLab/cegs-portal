from factory import Faker
from factory.django import DjangoModelFactory

from cegs_portal.search.models import File

from .experiment_factory import ExperimentFactory


class FileFactory(DjangoModelFactory):
    class Meta:
        model = File

    filename = Faker("file_path")
    description = Faker("text", max_nb_chars=4096)
    url = Faker("uri")
    size = 1_000_000
    category = None
    data_file_info = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)

        experiment = kwargs.get("experiment", None)
        if experiment is not None:
            obj.experiment = experiment
        else:
            obj.experiment = ExperimentFactory()

        obj.save()
        return obj
