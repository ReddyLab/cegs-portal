import os

import pytest
from django.core.files.storage import default_storage
from psycopg2.extras import NumericRange

from cegs_portal.get_expr_data.models import EXPR_DATA_DIR, ReoSourcesTargets
from cegs_portal.search.conftest import (  # noqa: F401 used as fixture in tests.py
    login_client,
    public_client,
)
from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory
from cegs_portal.search.models.tests.facet_factory import FacetValueFactory
from cegs_portal.search.models.tests.reg_effects_factory import RegEffectFactory


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_files():
    yield
    _, files = default_storage.listdir(EXPR_DATA_DIR)
    for file in files:
        default_storage.delete(os.path.join(EXPR_DATA_DIR, file))


def _reg_effects(public=True, archived=False) -> list[RegulatoryEffectObservation]:
    experiment = ExperimentFactory(accession_id="DCPEXPR00000002")
    analysis = experiment.analyses.first()
    facet_source = FacetValueFactory()
    facet_target = FacetValueFactory()
    facet_both = FacetValueFactory()

    effect_source = RegEffectFactory(
        sources=(
            DNAFeatureFactory(
                parent=None, chrom_name="chr1", location=NumericRange(10, 1_000), experiment_accession=None
            ),
            DNAFeatureFactory(
                parent=None, chrom_name="chr1", location=NumericRange(20_000, 111_000), experiment_accession=None
            ),
            DNAFeatureFactory(
                parent=None, chrom_name="chr2", location=NumericRange(22_222, 33_333), experiment_accession=None
            ),
        ),
        public=public,
        archived=archived,
        experiment=experiment,
        experiment_accession=experiment,
        analysis=analysis,
        facet_values=[facet_source],
    )
    effect_target = RegEffectFactory(
        targets=(
            DNAFeatureFactory(
                parent=None,
                chrom_name="chr1",
                name="LNLC-1",
                ensembl_id="ENSG01124619313",
                location=NumericRange(35_000, 40_000),
                experiment_accession=None,
            ),
        ),
        public=public,
        archived=archived,
        experiment=experiment,
        experiment_accession=experiment,
        analysis=analysis,
        facet_values=[facet_target],
    )
    effect_both = RegEffectFactory(
        sources=(
            DNAFeatureFactory(
                parent=None, chrom_name="chr1", location=NumericRange(11, 1_001), experiment_accession=None
            ),
            DNAFeatureFactory(
                parent=None, chrom_name="chr2", location=NumericRange(22_223, 33_334), experiment_accession=None
            ),
        ),
        targets=(
            DNAFeatureFactory(
                parent=None,
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
        facet_values=[facet_both],
    )
    ReoSourcesTargets.refresh_view()
    return (effect_source, effect_target, effect_both, facet_source, facet_target, facet_both, experiment)


@pytest.fixture
def reg_effects():
    return _reg_effects()


@pytest.fixture
def private_reg_effects():
    return _reg_effects(public=False)
