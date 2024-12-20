import pytest
from psycopg.types.range import Int4Range

from cegs_portal.search.models import DNAFeature, DNAFeatureType, GrnaType, PromoterType
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory
from cegs_portal.search.models.tests.facet_factory import (
    FacetFactory,
    FacetValueFactory,
)
from utils.file import FileMetadata


class MockExperimentMetadata:
    features = None
    parent_features = None

    def __init__(self):
        self.experiment = ExperimentFactory()
        self.accession_id = self.experiment.accession_id
        self.file_metadata = [
            FileMetadata({"file": "elements_file", "genome_assembly": "hg38"}, "/"),
            FileMetadata({"file": "elements_parent_file", "genome_assembly": "hg38"}, "/"),
        ]
        self.tested_elements_file = self.file_metadata[0]
        self.tested_elements_parent_file = self.file_metadata[1]

    def db_save(self):
        return self.experiment

    def db_del(self):
        pass


@pytest.fixture
def experiment_metadata():
    return MockExperimentMetadata()


@pytest.fixture(autouse=True)
def facets():
    grna_facet = FacetFactory(description="", name=DNAFeature.Facet.GRNA_TYPE.value)
    _ = FacetValueFactory(facet=grna_facet, value=GrnaType.POSITIVE_CONTROL.value)
    _ = FacetValueFactory(facet=grna_facet, value=GrnaType.NEGATIVE_CONTROL.value)
    _ = FacetValueFactory(facet=grna_facet, value=GrnaType.TARGETING.value)

    promoter_facet = FacetFactory(description="", name=DNAFeature.Facet.PROMOTER.value)
    _ = FacetValueFactory(facet=promoter_facet, value=PromoterType.PROMOTER.value)
    _ = FacetValueFactory(facet=promoter_facet, value=PromoterType.NON_PROMOTER.value)


@pytest.fixture(autouse=True)
def ccres():
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=Int4Range(100, 200))
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=Int4Range(300, 400))
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=Int4Range(500, 600))
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=Int4Range(700, 800))


@pytest.fixture(autouse=True)
def gene():
    _ = DNAFeatureFactory(
        feature_type=DNAFeatureType.GENE, chrom_name="chr1", location=Int4Range(1000, 2000), strand="+"
    )


@pytest.fixture(autouse=True)
def cleanup_gen_features():
    yield
    for feature in DNAFeature.objects.exclude(feature_type__in=[DNAFeatureType.CCRE, DNAFeatureType.GENE]).all():
        feature.delete()

    for ccre in DNAFeature.objects.filter(feature_type=DNAFeatureType.CCRE, misc__pseudo=True).all():
        ccre.delete()
