import factory
from factory import Faker, post_generation
from factory.django import DjangoModelFactory
from faker import Faker as F

from cegs_portal.search.models import (
    CellLine,
    Experiment,
    ExperimentDataFile,
    TissueType,
)


class CellLineFactory(DjangoModelFactory):
    class Meta:
        model = CellLine

    line_name = Faker("text", max_nb_chars=100)


class TissueTypeFactory(DjangoModelFactory):
    class Meta:
        model = TissueType

    tissue_type = Faker("text", max_nb_chars=100)


class ExperimentFactory(DjangoModelFactory):
    class Meta:
        model = Experiment
        django_get_or_create = ("name",)

    _faker = F()
    archived = Faker("boolean", chance_of_getting_true=90)
    description = Faker("text", max_nb_chars=4096)
    experiment_type = Faker("text", max_nb_chars=100)
    name = Faker("text", max_nb_chars=512)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = cls._faker.unique.hexify(text="DCPE^^^^^^^^", upper=True)
        obj.save()
        return obj

    @post_generation
    def other_files(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for file in extracted:
                self.other_files.add(file)  # pylint: disable=no-member

    @post_generation
    def data_files(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for file in extracted:
                self.data_files.add(file)  # pylint: disable=no-member


class ExperimentDataFileFactory(DjangoModelFactory):
    class Meta:
        model = ExperimentDataFile
        django_get_or_create = ("filename",)

    cell_line = Faker("text", max_nb_chars=100)
    description = Faker("text", max_nb_chars=4096)
    experiment = factory.SubFactory(ExperimentFactory)
    filename = Faker("text", max_nb_chars=512)
    ref_genome = Faker("text", max_nb_chars=20)
    ref_genome_patch = Faker("text", max_nb_chars=10)
    significance_measure = Faker("text", max_nb_chars=2048)

    @post_generation
    def cell_lines(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for line in extracted:
                self.cell_lines.add(line)  # pylint: disable=no-member

    @post_generation
    def tissue_types(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for tissue in extracted:
                self.tissue_types.add(tissue)  # pylint: disable=no-member
