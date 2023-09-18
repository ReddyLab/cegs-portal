import os

import pytest
from django.core.files.storage import default_storage
from psycopg2.extras import NumericRange

from cegs_portal.get_expr_data.models import (
    EXPR_DATA_DIR,
    ReoSourcesTargets,
    ReoSourcesTargetsSigOnly,
)
from cegs_portal.search.models import (
    EffectObservationDirectionType,
    RegulatoryEffectObservation,
)
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import (
    ExperimentDataFileInfoFactory,
    ExperimentFactory,
)
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
    experiment = ExperimentFactory(accession_id="DCPEXPR00000002")
    analysis = experiment.analyses.first()
    experiment_file_info = ExperimentDataFileInfoFactory()
    _analysis_file = FileFactory(analysis=analysis, data_file_info=experiment_file_info)  # noqa: F841

    sources = (
        DNAFeatureFactory(
            accession_id="DCPDHS00000000",
            chrom_name="chr1",
            location=NumericRange(10, 1_000),
            experiment_accession=None,
        ),
        DNAFeatureFactory(
            accession_id="DCPDHS00000001",
            chrom_name="chr1",
            location=NumericRange(20_000, 111_000),
            experiment_accession=None,
        ),
        DNAFeatureFactory(
            accession_id="DCPDHS00000002",
            chrom_name="chr2",
            location=NumericRange(22_222, 33_333),
            experiment_accession=None,
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

    effect_target = RegEffectFactory(
        targets=(
            DNAFeatureFactory(
                chrom_name="chr1",
                name="LNLC-1",
                ensembl_id="ENSG01124619313",
                location=NumericRange(35_000, 40_000),
                experiment_accession=None,
            ),
        ),
        facet_num_values={
            RegulatoryEffectObservation.Facet.EFFECT_SIZE.value: 2.0760384670056446,
            RegulatoryEffectObservation.Facet.RAW_P_VALUE.value: 7.19229500470051e-06,
            RegulatoryEffectObservation.Facet.SIGNIFICANCE.value: 0.057767530629869,
        },
        public=public,
        archived=archived,
        experiment=experiment,
        experiment_accession=experiment,
        analysis=analysis,
        facet_values=[depleted_facet],
    )

    effect_both = RegEffectFactory(
        sources=(
            DNAFeatureFactory(chrom_name="chr1", location=NumericRange(11, 1_001), experiment_accession=None),
            DNAFeatureFactory(chrom_name="chr2", location=NumericRange(22_223, 33_334), experiment_accession=None),
        ),
        targets=(
            DNAFeatureFactory(
                chrom_name="chr1",
                name="XUEQ-1",
                ensembl_id="ENSG01124619313",
                location=NumericRange(35_001, 40_001),
                experiment_accession=None,
            ),
        ),
        public=public,
        archived=archived,
        experiment=experiment,
        experiment_accession=experiment,
        analysis=analysis,
        facet_values=[nonsig_facet],
    )
    ReoSourcesTargets.refresh_view()
    ReoSourcesTargetsSigOnly.refresh_view()

    return (effect_source, effect_target, effect_both, enriched_facet, depleted_facet, nonsig_facet, experiment)


@pytest.fixture
def reg_effects():
    return _reg_effects()


@pytest.fixture
def private_reg_effects():
    return _reg_effects(public=False)
