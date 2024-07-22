from factory import Faker
from factory.django import DjangoModelFactory
from faker import Faker as F

from cegs_portal.search.models import ExperimentCollection


class ExperimentCollectionFactory(DjangoModelFactory):
    class Meta:
        model = ExperimentCollection

    _faker = F()
    archived = False
    public = True
    name = Faker("text", max_nb_chars=256)
    description = Faker("text", max_nb_chars=4096)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = kwargs.get("accession_id", cls._faker.unique.hexify(text="DCPEXCL^^^^^^^^^^", upper=True))
        obj.save()
        return obj
