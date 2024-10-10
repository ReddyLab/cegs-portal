import os

import pytest
from django.core.files.storage import default_storage
from psycopg.types.range import Int4Range

from cegs_portal.get_expr_data.models import (
    EXPR_DATA_DIR,
    ReoSourcesTargets,
    ReoSourcesTargetsSigOnly,
)
from cegs_portal.search.models import (
    DNAFeatureType,
    EffectObservationDirectionType,
    RegulatoryEffectObservation,
)
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory
from cegs_portal.search.models.tests.facet_factory import (
    FacetFactory,
    FacetValueFactory,
)
from cegs_portal.search.models.tests.file_factory import FileFactory
from cegs_portal.search.models.tests.reg_effects_factory import RegEffectFactory


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_files():
    yield
    _, files = default_storage.listdir(EXPR_DATA_DIR)
    for file in files:
        default_storage.delete(os.path.join(EXPR_DATA_DIR, file))


def _reg_effects(public=True, archived=False) -> list[RegulatoryEffectObservation]:
    direction_facet = FacetFactory(description="", name=RegulatoryEffectObservation.Facet.DIRECTION.value)
    enriched_facet = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.ENRICHED.value)
    depleted_facet = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.DEPLETED.value)
    nonsig_facet = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.NON_SIGNIFICANT.value)
    experiment = ExperimentFactory(accession_id="DCPEXPR0000000002")
    analysis = experiment.analyses.first()
    _analysis_file = FileFactory(analysis=analysis)  # noqa: F841

    sources = (
        DNAFeatureFactory(
            accession_id="DCPDHS0000000000",
            chrom_name="chr1",
            location=Int4Range(10, 1_000),
            experiment_accession=None,
            feature_type=DNAFeatureType.GRNA,
        ),
        DNAFeatureFactory(
            accession_id="DCPDHS0000000001",
            chrom_name="chr1",
            location=Int4Range(20_000, 111_000),
            experiment_accession=None,
            feature_type=DNAFeatureType.DHS,
        ),
        DNAFeatureFactory(
            accession_id="DCPDHS0000000002",
            chrom_name="chr2",
            location=Int4Range(22_222, 33_333),
            experiment_accession=None,
            feature_type=DNAFeatureType.CAR,
        ),
    )
    for source in sources:
        source.save()

    effect_source = RegEffectFactory(
        sources=sources,
        public=public,
        archived=archived,
        experiment=experiment,
        experiment_accession=experiment,
        analysis=analysis,
        facet_values=[enriched_facet],
    )

    effect_both = RegEffectFactory(
        sources=(
            DNAFeatureFactory(
                chrom_name="chr1",
                location=Int4Range(11, 1_001),
                experiment_accession=None,
                feature_type=DNAFeatureType.GRNA,
            ),
            DNAFeatureFactory(
                chrom_name="chr2",
                location=Int4Range(22_223, 33_334),
                experiment_accession=None,
                feature_type=DNAFeatureType.CAR,
            ),
        ),
        targets=(
            DNAFeatureFactory(
                chrom_name="chr1",
                name="XUEQ-1",
                ensembl_id="ENSG01124619313",
                location=Int4Range(35_001, 40_001),
                experiment_accession=None,
                feature_type=DNAFeatureType.GENE,
            ),
        ),
        public=public,
        archived=archived,
        experiment=experiment,
        experiment_accession=experiment,
        analysis=analysis,
        facet_values=[nonsig_facet],
    )
    ReoSourcesTargets.load_analysis(analysis.accession_id)
    ReoSourcesTargetsSigOnly.load_analysis(analysis.accession_id)

    return (effect_source, effect_both, enriched_facet, depleted_facet, nonsig_facet, experiment)


@pytest.fixture
def reg_effects():
    return _reg_effects()


@pytest.fixture
def private_reg_effects():
    return _reg_effects(public=False)
