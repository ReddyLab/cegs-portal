from typing import Iterable

import pytest
from django.db.models import Manager

from cegs_portal.search.models import (
    DNAFeature,
    EffectDirectionType,
    Experiment,
    ExperimentDataFile,
    Facet,
    File,
    RegulatoryEffect,
)
from cegs_portal.search.models.tests.dna_feature_factory import DNAFeatureFactory
from cegs_portal.search.models.tests.experiment_factory import (
    CellLineFactory,
    ExperimentDataFileFactory,
    ExperimentFactory,
    TissueTypeFactory,
)
from cegs_portal.search.models.tests.facet_factory import (
    FacetFactory,
    FacetValueFactory,
)
from cegs_portal.search.models.tests.file_factory import FileFactory
from cegs_portal.search.models.tests.reg_effects_factory import RegEffectFactory
from cegs_portal.utils.pagination_types import MockPaginator, Pageable


@pytest.fixture
def experiment() -> Experiment:
    return ExperimentFactory(other_files=(other_file(), other_file()), data_files=(data_file(),))


@pytest.fixture
def experiments() -> Iterable[Experiment]:
    e1 = ExperimentFactory(other_files=(other_file(), other_file()), data_files=(data_file(),))
    e2 = ExperimentFactory(other_files=(other_file(), other_file()), data_files=(data_file(),))
    e3 = ExperimentFactory(other_files=(other_file(), other_file()), data_files=(data_file(),))
    return [e1, e2, e3]


def data_file() -> ExperimentDataFile:
    return ExperimentDataFileFactory(cell_lines=(CellLineFactory(),), tissue_types=(TissueTypeFactory(),))


@pytest.fixture(name="data_file")
def df() -> ExperimentDataFile:
    return data_file()


def other_file() -> File:
    return FileFactory()


@pytest.fixture(name="other_file")
def of() -> File:
    return other_file()


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
def reg_effect() -> RegulatoryEffect:
    direction_facet = FacetFactory(description="", name=RegulatoryEffect.Facet.DIRECTION.value)
    direction = FacetValueFactory(facet=direction_facet, value=EffectDirectionType.ENRICHED)
    effect = RegEffectFactory(
        sources=(DNAFeatureFactory(parent=None), DNAFeatureFactory(parent=None)), facet_values=(direction,)
    )
    effect.experiment.data_files.add(
        ExperimentDataFileFactory(cell_lines=(CellLineFactory(),), tissue_types=(TissueTypeFactory(),))
    )
    return effect


@pytest.fixture
def facets() -> Manager[Facet]:
    f1 = FacetFactory()
    f2 = FacetFactory()
    _ = FacetValueFactory(facet=f1)
    _ = FacetValueFactory(facet=f1)
    _ = FacetValueFactory(facet=f2)
    _ = FacetValueFactory(facet=f2)
    return Facet.objects
