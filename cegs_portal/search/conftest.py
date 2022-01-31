from typing import Iterable

import pytest
from django.db.models import Manager

from cegs_portal.search.models import (
    Experiment,
    ExperimentDataFile,
    Facet,
    Feature,
    FeatureAssembly,
    File,
    RegulatoryEffect,
)
from cegs_portal.search.models.dna_region import DNARegion
from cegs_portal.search.models.tests.dna_region_factory import DNARegionFactory
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
from cegs_portal.search.models.tests.features_factory import (
    FeatureAssemblyFactory,
    FeatureFactory,
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
def region() -> DNARegion:
    return DNARegionFactory()


@pytest.fixture
def regions() -> Pageable[DNARegion]:
    paginator = MockPaginator(
        [
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
            DNARegionFactory(),
        ],
        3,
    )
    return paginator.page(2)


@pytest.fixture
def region_tuple() -> tuple[DNARegion, Iterable]:
    return (DNARegionFactory(), [])


@pytest.fixture
def feature_assemblies() -> Iterable[FeatureAssembly]:
    f1 = FeatureFactory(parent=None)
    f2 = FeatureFactory(parent=None)
    f3 = FeatureFactory(parent=None)
    fa1a = FeatureAssemblyFactory(feature=f1)
    fa1b = FeatureAssemblyFactory(feature=f1)
    fa2a = FeatureAssemblyFactory(feature=f2)
    fa3a = FeatureAssemblyFactory(feature=f3)
    fa3b = FeatureAssemblyFactory(feature=f3)
    return [fa1a, fa1b, fa2a, fa3a, fa3b]


@pytest.fixture
def features() -> list[Feature]:
    f1 = FeatureFactory(parent=None)
    f2 = FeatureFactory(parent=None)
    f3 = FeatureFactory(parent=None)
    _ = [FeatureAssemblyFactory(feature=f1), FeatureAssemblyFactory(feature=f1)]
    _ = [FeatureAssemblyFactory(feature=f2)]
    _ = [FeatureAssemblyFactory(feature=f3), FeatureAssemblyFactory(feature=f3)]
    return [f1, f2, f3]


@pytest.fixture
def feature() -> Feature:
    parent = FeatureFactory(parent=None)
    f1 = FeatureFactory(parent=parent)
    _ = [FeatureAssemblyFactory(feature=f1), FeatureAssemblyFactory(feature=f1)]
    return f1


@pytest.fixture
def assembly() -> FeatureAssembly:
    f1 = FeatureFactory(parent=None)
    return FeatureAssemblyFactory(feature=f1)


@pytest.fixture
def reg_effect() -> RegulatoryEffect:
    effect = RegEffectFactory(sources=(DNARegionFactory(), DNARegionFactory()))
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
