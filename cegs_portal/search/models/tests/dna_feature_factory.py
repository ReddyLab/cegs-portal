import random

import factory
from factory import Faker, post_generation
from factory.django import DjangoModelFactory
from faker import Faker as F
from psycopg.types.range import Int4Range

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
    chrom_name = Faker("numerify", text=r"chr1%")
    _start = random.randint(0, 1000000)
    _end = _start + random.randint(1, 1000000)
    location = Int4Range(_start, _end)
    strand = random.choice(["+", "-", None])
    ref_genome = "hg38"
    ref_genome_patch = Faker("numerify", text="##")
    feature_type = str(random.choice(list(DNAFeatureType)))
    feature_subtype = Faker("text", max_nb_chars=50)
    ids = {"id_type": "id_value"}
    misc = {"other id": "id value"}
    source_file = factory.SubFactory(FileFactory)

    parent = None
    closest_gene = None

    significant_reo = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # in DNAFeatureSearch#loc_search the "effect_directions" property adds
        # an "effect_directions" annotation to DNAFeature objects
        if "facet_value_agg" in kwargs:
            facet_value_agg = kwargs["facet_value_agg"]
            del kwargs["facet_value_agg"]
        else:
            facet_value_agg = None

        obj = model_class(*args, **kwargs)
        if "accession_id" not in kwargs:
            obj.accession_id = cls._faker.unique.hexify(text="DCPGENE^^^^^^^^^^", upper=True)
            obj.save()

        if facet_value_agg is not None:
            setattr(obj, "facet_value_agg", facet_value_agg)

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
            return random.randint(-10000, 10000)
        return None

    @post_generation
    def facet_values(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for value in extracted:
                self.facet_values.add(value)  # pylint: disable=no-member
