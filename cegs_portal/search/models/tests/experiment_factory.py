import factory
from factory import Faker, post_generation
from factory.django import DjangoModelFactory
from faker import Faker as F

from cegs_portal.search.models import (
    Biosample,
    CellLine,
    Experiment,
    ExperimentDataFileInfo,
    TissueType,
)
from cegs_portal.search.models.tests.analysis_factory import AnalysisFactory


class TissueTypeFactory(DjangoModelFactory):
    class Meta:
        model = TissueType

    _faker = F()

    name = Faker("text", max_nb_chars=100)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = cls._faker.unique.hexify(text="DCPTT^^^^^^^^", upper=True)
        obj.save()
        return obj


class CellLineFactory(DjangoModelFactory):
    class Meta:
        model = CellLine

    _faker = F()

    name = Faker("text", max_nb_chars=100)
    tissue_type = factory.SubFactory(TissueTypeFactory)
    tissue_type_name = factory.SelfAttribute("tissue_type.name")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = cls._faker.unique.hexify(text="DCPCL^^^^^^^^", upper=True)
        obj.save()
        return obj


class BiosampleFactory(DjangoModelFactory):
    class Meta:
        model = Biosample

    _faker = F()

    cell_line = factory.SubFactory(CellLineFactory)
    cell_line_name = factory.SelfAttribute("cell_line.name")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = cls._faker.unique.hexify(text="DCPBIOS^^^^^^^^", upper=True)
        obj.save()
        return obj


class ExperimentFactory(DjangoModelFactory):
    class Meta:
        model = Experiment
        django_get_or_create = ("name",)

    _faker = F()
    archived = False
    public = True
    description = Faker("text", max_nb_chars=4096)
    experiment_type = Faker("text", max_nb_chars=100)
    name = Faker("text", max_nb_chars=512)
    analyses = factory.RelatedFactory(AnalysisFactory, factory_related_name="experiment")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = kwargs.get("accession_id", cls._faker.unique.hexify(text="DCPEXPR^^^^^^^^", upper=True))
        obj.save()
        return obj

    @post_generation
    def biosamples(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for sample in extracted:
                self.biosamples.add(sample)  # pylint: disable=no-member


class ExperimentDataFileInfoFactory(DjangoModelFactory):
    class Meta:
        model = ExperimentDataFileInfo

    ref_genome = "GRCh38"
    ref_genome_patch = "0"
    significance_measure = Faker("text", max_nb_chars=2048)
    p_value_threshold = 0.05
