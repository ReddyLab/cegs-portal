import random

import factory
from factory import Faker
from factory.django import DjangoModelFactory
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, DNAFeatureType
from cegs_portal.search.models.tests.file_factory import FileFactory


class DNAFeatureFactory(DjangoModelFactory):
    class Meta:
        model = DNAFeature
        django_get_or_create = ("name", "ensembl_id")

    ensembl_id = Faker("text", max_nb_chars=50)
    cell_line = Faker("text", max_nb_chars=50)
    chrom_name = Faker("text", max_nb_chars=10)
    closest_gene_distance = random.randint(0, 10000)
    closest_gene_name = Faker("text", max_nb_chars=50)
    ids = {"id_type": "id_value"}
    _start = random.randint(0, 1000000)
    _end = _start + random.randint(1, 1000000)
    location = NumericRange(_start, _end)
    name = Faker("text", max_nb_chars=50)
    strand = random.choice(["+", "-", None])
    ref_genome = Faker("text", max_nb_chars=20)
    ref_genome_patch = Faker("text", max_nb_chars=10)
    feature_type = random.choice(list(DNAFeatureType))
    feature_subtype = Faker("text", max_nb_chars=50)
    misc = {"other id": "id value"}
    source = factory.SubFactory(FileFactory)

    # Be careful when creating a set of DNAFeatureFactory. The "parent" values should be explicit and
    # there should always be a DNAFeatureFactory(parent=None) for each stack of DNAFeatureFactories
    # so pytest doesn't infinitely recurse
    parent = factory.SubFactory("cegs_portal.search.models.tests.dna_feature_factory.DNAFeatureFactory")
