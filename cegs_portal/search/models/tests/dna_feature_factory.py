import random

import factory
from factory import Faker, post_generation
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
    closest_gene_distance = random.randint(0, 10000)
    closest_gene_name = Faker("lexify", text="????-1", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    ids = {"id_type": "id_value"}
    _start = random.randint(0, 1000000)
    _end = _start + random.randint(1, 1000000)
    location = NumericRange(_start, _end)
    strand = random.choice(["+", "-", None])
    ref_genome = Faker("text", max_nb_chars=20)
    ref_genome_patch = Faker("numerify", text="##")
    feature_type = random.choice(list(DNAFeatureType))
    feature_subtype = Faker("text", max_nb_chars=50)
    misc = {"other id": "id value"}
    source_file = factory.SubFactory(FileFactory)

    # Be careful when creating a set of DNAFeatureFactory. The "parent" values should be explicit and
    # there should always be a DNAFeatureFactory(parent=None) for each stack of DNAFeatureFactories
    # so pytest doesn't infinitely recurse
    parent = factory.SubFactory("cegs_portal.search.models.tests.dna_feature_factory.DNAFeatureFactory")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        if "accession_id" not in kwargs:
            obj.accession_id = cls._faker.unique.hexify(text="DCPGENE^^^^^^^^", upper=True)
            obj.save()
        return obj

    @post_generation
    def parent_accession_id(self, create, extracted, **kwargs):
        if self.parent is not None:
            self.parent_accession_id = self.parent.accession_id  # pylint: disable=no-member
        else:
            self.parent_accession_id = None
