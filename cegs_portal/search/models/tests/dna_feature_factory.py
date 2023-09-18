import random

import factory
from factory import Faker
from factory.django import DjangoModelFactory
from faker import Faker as F
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, DNAFeatureType
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory
from cegs_portal.search.models.tests.file_factory import FileFactory


class DNAFeatureFactory(DjangoModelFactory):
    class Meta:
        model = DNAFeature
        django_get_or_create = ("name", "ensembl_id")

    _faker = F()
    archived = False
    public = True
    experiment_accession = factory.SubFactory(ExperimentFactory)
    ensembl_id = _faker.unique.numerify(text="ENSG###########")
    name = Faker("lexify", text="????-1", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    cell_line = Faker("text", max_nb_chars=50)
    chrom_name = Faker("numerify", text=r"chr%%")
    _start = random.randint(0, 1000000)
    _end = _start + random.randint(1, 1000000)
    location = NumericRange(_start, _end)
    strand = random.choice(["+", "-", None])
    ref_genome = Faker("text", max_nb_chars=20)
    ref_genome_patch = Faker("numerify", text="##")
    feature_type = random.choice(list(DNAFeatureType))
    feature_subtype = Faker("text", max_nb_chars=50)
    ids = {"id_type": "id_value"}
    misc = {"other id": "id value"}
    source_file = factory.SubFactory(FileFactory)

    parent = None
    closest_gene = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        if "accession_id" not in kwargs:
            obj.accession_id = cls._faker.unique.hexify(text="DCPGENE^^^^^^^^", upper=True)
            obj.save()
        return obj

    @factory.lazy_attribute
    def parent_accession_id(self):
        if self.parent:
            return self.parent.accession_id  # pylint: disable=no-member

        return None

    @factory.lazy_attribute
    def closest_gene_name(self):
        if self.closest_gene:
            return self.closest_gene.name
        return None

    @factory.lazy_attribute
    def closest_gene_ensembl_id(self):
        if self.closest_gene:
            return self.closest_gene.ensembl_id
        return None

    @factory.lazy_attribute
    def closest_gene_distance(self):
        if self.closest_gene:
            return random.randint(0, 10000)
        return None
