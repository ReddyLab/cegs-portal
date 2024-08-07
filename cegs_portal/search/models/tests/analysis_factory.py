from factory import Faker, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker as F

from cegs_portal.search.models import Analysis


class AnalysisFactory(DjangoModelFactory):
    class Meta:
        model = Analysis
        django_get_or_create = ("name",)

    _faker = F()
    archived = False
    public = True
    name = Faker("text", max_nb_chars=512)
    description = Faker("text", max_nb_chars=4096)
    experiment = SubFactory("cegs_portal.search.models.tests.experiment_factory.ExperimentFactory")
    genome_assembly = "hg38"  # The default ref genome when searching
    genome_assembly_patch = "0"
    p_value_threshold = 0.05
    p_value_adj_method = "unknown"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = kwargs.get("accession_id", cls._faker.unique.hexify(text="DCPAN^^^^^^^^^^", upper=True))
        obj.save()
        return obj
