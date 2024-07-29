import pytest
from psycopg2.extras import NumericRange

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import (
    DNAFeature,
    DNAFeatureType,
    EffectObservationDirectionType,
    Experiment,
    Facet,
    GrnaType,
    PromoterType,
    RegulatoryEffectObservation,
)
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory
from cegs_portal.search.models.tests.facet_factory import (
    FacetFactory,
    FacetValueFactory,
)
from cegs_portal.uploads.data_loading.file import FileMetadata


class MockExperimentMetadata:
    features = None
    parent_features = None

    def __init__(self):
        self.experiment = ExperimentFactory()
        self.assay = "scCERES"
        self.accession_id = self.experiment.accession_id
        self.tested_elements_file = FileMetadata(
            {
                "description": "test file",
                "filename": "elements_file",
                "file_location": "elements_file",
                "genome_assembly": "hg38",
            }
        )
        self.source_type = DNAFeatureType.GRNA.value
        self.parent_source_type = DNAFeatureType.DHS.value

    def db_save(self):
        return self.experiment

    def db_del(self):
        pass


@pytest.fixture
def experiment_metadata():
    return MockExperimentMetadata()


@pytest.fixture
def add_experiment_client(django_user_model):
    return SearchClient(user_model=django_user_model, username="user2", password="bar", permissions=["add_experiment"])


@pytest.fixture(autouse=True)
def genes() -> tuple[DNAFeature, DNAFeature, DNAFeature]:
    f1 = DNAFeatureFactory(
        name="ACAP3", ensembl_id="ENSG00000131584", feature_type="DNAFeatureType.GENE", chrom_name="chr1", strand="+"
    )
    f2 = DNAFeatureFactory(
        name="AL627309.1",
        ensembl_id="ENSG00000237683",
        feature_type="DNAFeatureType.GENE",
        chrom_name="chr1",
        strand="-",
    )
    f3 = DNAFeatureFactory(
        name="AL590822.1",
        ensembl_id="ENSG00000203301",
        feature_type="DNAFeatureType.GENE",
        chrom_name="chr1",
        strand="-",
    )

    return f1, f2, f3


@pytest.fixture(autouse=True)
def facets() -> list[Facet]:
    direction_facet = FacetFactory(description="", name=RegulatoryEffectObservation.Facet.DIRECTION.value)
    _ = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.ENRICHED.value)
    _ = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.DEPLETED.value)
    _ = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.NON_SIGNIFICANT.value)

    grna_type_facet = FacetFactory(description="", name=DNAFeature.Facet.GRNA_TYPE.value)
    _ = FacetValueFactory(facet=grna_type_facet, value=GrnaType.NEGATIVE_CONTROL.value)
    _ = FacetValueFactory(facet=grna_type_facet, value=GrnaType.POSITIVE_CONTROL.value)
    _ = FacetValueFactory(facet=grna_type_facet, value=GrnaType.TARGETING.value)

    promoter_facet = FacetFactory(description="", name=DNAFeature.Facet.PROMOTER.value)
    _ = FacetValueFactory(facet=promoter_facet, value=PromoterType.NON_PROMOTER.value)
    _ = FacetValueFactory(facet=promoter_facet, value=PromoterType.PROMOTER.value)

    assay_facet = FacetFactory(description="", name=Experiment.Facet.ASSAYS.value)
    _ = FacetValueFactory(facet=assay_facet, value="Perturb-Seq")
    _ = FacetValueFactory(facet=assay_facet, value="Proliferation Screen")
    _ = FacetValueFactory(facet=assay_facet, value="ATAC-STARR-seq")

    source_type_facet = FacetFactory(description="", name=Experiment.Facet.SOURCE_TYPES.value)
    _ = FacetValueFactory(facet=source_type_facet, value="gRNA")
    _ = FacetValueFactory(facet=source_type_facet, value="cCRE")
    _ = FacetValueFactory(facet=source_type_facet, value="CAR")
    _ = FacetValueFactory(facet=source_type_facet, value="DHS")

    cell_line_facet = FacetFactory(description="", name=Experiment.Facet.CELL_LINE.value)
    _ = FacetValueFactory(facet=cell_line_facet, value="iPSC")
    _ = FacetValueFactory(facet=cell_line_facet, value="K562")
    _ = FacetValueFactory(facet=cell_line_facet, value="NPC")
    _ = FacetValueFactory(facet=cell_line_facet, value="CD8")

    tissue_type_facet = FacetFactory(description="", name=Experiment.Facet.TISSUE_TYPE.value)
    _ = FacetValueFactory(facet=tissue_type_facet, value="Stem")
    _ = FacetValueFactory(facet=tissue_type_facet, value="Bone Marrow")
    _ = FacetValueFactory(facet=tissue_type_facet, value="T Cell")

    return [
        direction_facet,
        grna_type_facet,
        promoter_facet,
        assay_facet,
        source_type_facet,
        cell_line_facet,
        tissue_type_facet,
    ]


@pytest.fixture(autouse=True)
def ccres():
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=NumericRange(100, 200))
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=NumericRange(300, 400))
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=NumericRange(500, 600))
    _ = DNAFeatureFactory(feature_type=DNAFeatureType.CCRE, chrom_name="chr1", location=NumericRange(700, 800))


@pytest.fixture(autouse=True)
def cleanup_gen_features():
    yield
    for feature in DNAFeature.objects.exclude(feature_type__in=[DNAFeatureType.CCRE, DNAFeatureType.GENE]).all():
        feature.delete()

    for ccre in DNAFeature.objects.filter(feature_type=DNAFeatureType.CCRE, misc__pseudo=True).all():
        ccre.delete()
