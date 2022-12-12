from typing import Iterable, Tuple

import pytest
from django.db.models import Manager
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    Biosample,
    DNAFeature,
    EffectObservationDirectionType,
    Experiment,
    ExperimentDataFile,
    Facet,
    File,
    RegulatoryEffectObservation,
)
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import (
    BiosampleFactory,
    ExperimentDataFileFactory,
    ExperimentFactory,
)
from cegs_portal.search.models.tests.facet_factory import (
    FacetFactory,
    FacetValueFactory,
)
from cegs_portal.search.models.tests.file_factory import FileFactory
from cegs_portal.search.models.tests.reg_effects_factory import RegEffectFactory
from cegs_portal.users.conftest import group_extension  # noqa: F401
from cegs_portal.utils.pagination_types import MockPaginator, Pageable


@pytest.fixture
def experiment() -> Experiment:
    e = ExperimentFactory(other_files=(other_file(), other_file()))
    e.data_files.set(((data_file(e),)))
    return e


@pytest.fixture
def private_experiment() -> Experiment:
    e = ExperimentFactory(other_files=(other_file(), other_file()), public=False)
    e.data_files.set(((data_file(e),)))
    return e


@pytest.fixture
def archived_experiment() -> Experiment:
    e = ExperimentFactory(other_files=(other_file(), other_file()), archived=True)
    e.data_files.set(((data_file(e),)))
    return e


@pytest.fixture
def access_control_experiments() -> Tuple[Experiment]:
    e1 = ExperimentFactory(other_files=(other_file(), other_file()))
    e1.data_files.set(((data_file(e1),)))
    e2 = ExperimentFactory(other_files=(other_file(), other_file()), public=False)
    e2.data_files.set(((data_file(e2),)))
    e3 = ExperimentFactory(other_files=(other_file(), other_file()), archived=True)
    e3.data_files.set(((data_file(e3),)))

    return (e1, e2, e3)


@pytest.fixture
def paged_experiments() -> Pageable[Experiment]:
    e1 = ExperimentFactory(other_files=(other_file(), other_file()), biosamples=(BiosampleFactory(),))
    e1.data_files.set(((data_file(e1),)))
    e2 = ExperimentFactory(other_files=(other_file(), other_file()), biosamples=(BiosampleFactory(),))
    e2.data_files.set(((data_file(e2),)))
    e3 = ExperimentFactory(other_files=(other_file(), other_file()), biosamples=(BiosampleFactory(),))
    e3.data_files.set(((data_file(e3),)))
    e4 = ExperimentFactory(other_files=(other_file(), other_file()), biosamples=(BiosampleFactory(),))
    e4.data_files.set(((data_file(e4),)))
    e5 = ExperimentFactory(other_files=(other_file(), other_file()), biosamples=(BiosampleFactory(),))
    e5.data_files.set(((data_file(e5),)))
    e6 = ExperimentFactory(other_files=(other_file(), other_file()), biosamples=(BiosampleFactory(),))
    e6.data_files.set(((data_file(e6),)))
    experiments = sorted([e1, e2, e3, e4, e5, e6], key=lambda x: x.accession_id)
    pages = MockPaginator(experiments, 3)
    return pages.page(1)


def data_file(experiment=None) -> ExperimentDataFile:
    return ExperimentDataFileFactory(experiment=experiment)


@pytest.fixture(name="data_file")
def df() -> ExperimentDataFile:
    return data_file()


def other_file() -> File:
    return FileFactory()


@pytest.fixture(name="other_file")
def of() -> File:
    return other_file()


@pytest.fixture
def biosample() -> Biosample:
    return BiosampleFactory()


@pytest.fixture
def feature_pages() -> Pageable[DNAFeature]:
    paginator: MockPaginator[DNAFeature] = MockPaginator(
        [
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
            DNAFeatureFactory(parent=None),
        ],
        3,
    )
    return paginator.page(2)


@pytest.fixture
def features() -> Iterable[DNAFeature]:
    f1 = DNAFeatureFactory(parent=None)
    f2 = DNAFeatureFactory(parent=None)
    f3 = DNAFeatureFactory(parent=None)
    f4 = DNAFeatureFactory(parent=None)
    f5 = DNAFeatureFactory(parent=None)
    return [f1, f2, f3, f4, f5]


@pytest.fixture
def feature() -> DNAFeature:
    return DNAFeatureFactory(parent=None)


@pytest.fixture
def private_feature() -> DNAFeature:
    return DNAFeatureFactory(parent=None, public=False)


@pytest.fixture
def archived_feature() -> DNAFeature:
    return DNAFeatureFactory(parent=None, archived=True)


@pytest.fixture
def nearby_feature_mix() -> Tuple[DNAFeature]:
    pub_feature = DNAFeatureFactory(parent=None)
    private_feature = DNAFeatureFactory(
        parent=None,
        chrom_name=pub_feature.chrom_name,
        location=NumericRange(pub_feature.location.lower + 1000, pub_feature.location.upper + 1000),
        public=False,
    )
    archived_feature = DNAFeatureFactory(
        parent=None,
        chrom_name=pub_feature.chrom_name,
        location=NumericRange(private_feature.location.lower + 1000, private_feature.location.upper + 1000),
        archived=True,
    )

    return (pub_feature, private_feature, archived_feature)


def _reg_effect(public=True, archived=False) -> RegulatoryEffectObservation:
    direction_facet = FacetFactory(description="", name=RegulatoryEffectObservation.Facet.DIRECTION.value)
    direction = FacetValueFactory(facet=direction_facet, value=EffectObservationDirectionType.ENRICHED)
    effect = RegEffectFactory(
        sources=(DNAFeatureFactory(parent=None), DNAFeatureFactory(parent=None)),
        facet_values=(direction,),
        public=public,
        archived=archived,
    )
    effect.experiment.biosamples.add(BiosampleFactory())
    effect.experiment.data_files.add(ExperimentDataFileFactory())
    return effect


@pytest.fixture
def reg_effect() -> RegulatoryEffectObservation:
    return _reg_effect()


@pytest.fixture
def private_reg_effect() -> RegulatoryEffectObservation:
    return _reg_effect(public=False)


@pytest.fixture
def archived_reg_effect() -> RegulatoryEffectObservation:
    return _reg_effect(archived=True)


@pytest.fixture
def source_reg_effects():
    source = DNAFeatureFactory(parent=None)

    reo1 = RegEffectFactory(
        sources=(source,),
    )
    reo2 = RegEffectFactory(
        sources=(source,),
    )
    reo3 = RegEffectFactory(
        sources=(source,),
    )
    return {
        "source": source,
        "effects": [reo1, reo2, reo3],
    }


@pytest.fixture
def target_reg_effects():
    target = DNAFeatureFactory(parent=None)

    reo1 = RegEffectFactory(
        targets=(target,),
    )
    reo2 = RegEffectFactory(
        targets=(target,),
    )
    reo3 = RegEffectFactory(
        targets=(target,),
    )
    return {
        "target": target,
        "effects": [reo1, reo2, reo3],
    }


@pytest.fixture
def facets() -> Manager[Facet]:
    f1 = FacetFactory()
    f2 = FacetFactory()
    _ = FacetValueFactory(facet=f1)
    _ = FacetValueFactory(facet=f1)
    _ = FacetValueFactory(facet=f2)
    _ = FacetValueFactory(facet=f2)
    return Facet.objects


@pytest.fixture
def paged_source_reg_effects() -> Pageable[RegulatoryEffectObservation]:
    source = DNAFeatureFactory(parent=None)

    paginator: MockPaginator[RegulatoryEffectObservation] = MockPaginator(
        [
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
            RegEffectFactory(
                sources=(source,),
            ),
        ],
        2,
    )
    return paginator.page(2)
