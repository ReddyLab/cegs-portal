import random

import factory
from factory import Faker
from factory.django import DjangoModelFactory
from psycopg2.extras import NumericRange

from cegs_portal.search.models import Feature, FeatureAssembly


class FeatureFactory(DjangoModelFactory):
    class Meta:
        model = Feature
        django_get_or_create = ("ensembl_id",)

    ensembl_id = Faker("text", max_nb_chars=50)
    feature_type = Faker("text", max_nb_chars=50)
    feature_subtype = Faker("text", max_nb_chars=50)
    misc = {"other id": "id value"}

    # Be careful when creating a set of FeatureFactory. The "parent" values should be explicit and
    # there should always be a FeatureFactory(parent=None) for each stack of FeatureFactories
    # so pytest doesn't infinitely recurse
    parent = factory.SubFactory("cegs_portal.search.models.tests.features_factory.FeatureFactory")


class FeatureAssemblyFactory(DjangoModelFactory):
    class Meta:
        model = FeatureAssembly
        django_get_or_create = ("name",)

    chrom_name = Faker("text", max_nb_chars=10)
    ids = {"id_type": "id_value"}
    _start = random.randint(0, 1000000)
    _end = _start + random.randint(1, 1000000)
    location = NumericRange(_start, _end)
    name = Faker("text", max_nb_chars=50)
    strand = random.choice(["+", "-", None])
    ref_genome = Faker("text", max_nb_chars=20)
    ref_genome_patch = Faker("text", max_nb_chars=10)
    feature = factory.SubFactory(FeatureFactory, parent=None)
    feature_type = Faker("text", max_nb_chars=50)