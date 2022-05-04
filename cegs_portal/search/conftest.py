from typing import Iterable

import pytest
from django.db.models import Manager

from cegs_portal.search.models import (
    EffectDirectionType,
    Experiment,
    ExperimentDataFile,
    Facet,
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
from cegs_portal.search.models.tests.features_factory import FeatureAssemblyFactory
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
    paginator: MockPaginator[DNARegion] = MockPaginator(
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
    f1 = FeatureAssemblyFactory(parent=None)
    f2 = FeatureAssemblyFactory(parent=None)
    f3 = FeatureAssemblyFactory(parent=None)
    f4 = FeatureAssemblyFactory(parent=None)
    f5 = FeatureAssemblyFactory(parent=None)
    return [f1, f2, f3, f4, f5]


@pytest.fixture
def assembly() -> FeatureAssembly:
    return FeatureAssemblyFactory(parent=None)


@pytest.fixture
def reg_effect() -> RegulatoryEffect:
    direction_facet = FacetFactory(description="", name=RegulatoryEffect.Facet.DIRECTION.value)
    direction = FacetValueFactory(facet=direction_facet, value=EffectDirectionType.ENRICHED)
    effect = RegEffectFactory(sources=(DNARegionFactory(), DNARegionFactory()), facet_values=(direction,))
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
