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


@pytest.fixture
def experiment() -> Experiment:
    return ExperimentFactory(other_files=(other_file(), other_file()), data_files=(data_file(),))


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
def regions() -> list[DNARegion]:
    return [DNARegionFactory(), DNARegionFactory(), DNARegionFactory()]


@pytest.fixture
def region_tuple() -> tuple[DNARegion, Iterable]:
    return (DNARegionFactory(), [])


@pytest.fixture
def feature() -> Feature:
    parent = FeatureFactory(parent=None)
    return FeatureFactory(parent=parent)


@pytest.fixture
def assembly() -> FeatureAssembly:
    return FeatureAssemblyFactory()


@pytest.fixture
def reg_effect() -> RegulatoryEffect:
    effect = RegEffectFactory()
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
