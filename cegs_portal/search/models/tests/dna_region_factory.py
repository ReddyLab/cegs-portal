import random

import factory
from factory import Faker
from factory.django import DjangoModelFactory
from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNARegion
from cegs_portal.search.models.tests.features_factory import (
    FeatureAssemblyFactory,
    FeatureFactory,
)
from cegs_portal.search.models.tests.file_factory import FileFactory


class DNARegionFactory(DjangoModelFactory):
    class Meta:
        model = DNARegion

    cell_line = Faker("text", max_nb_chars=50)
    chrom_name = Faker("text", max_nb_chars=10)
    closest_gene_assembly = factory.SubFactory(FeatureAssemblyFactory)
    closest_gene = factory.SubFactory(FeatureFactory, parent=None)
    closest_gene_distance = random.randint(0, 10000)
    closest_gene_name = Faker("text", max_nb_chars=50)
    _start = random.randint(0, 1000000)
    _end = _start + random.randint(1, 1000000)
    location = NumericRange(_start, _end)
    misc = {"key": "value"}
    ref_genome = Faker("text", max_nb_chars=20)
    ref_genome_patch = Faker("text", max_nb_chars=10)
    region_type = Faker("text", max_nb_chars=50)
    source = factory.SubFactory(FileFactory)
    strand = random.choice(["+", "-", None])
