import pytest

from cegs_portal.search.models import Experiment, ExperimentDataFile, File
from cegs_portal.search.models.tests.experiment_factory import (
    CellLineFactory,
    ExperimentDataFileFactory,
    ExperimentFactory,
    TissueTypeFactory,
)
from cegs_portal.search.models.tests.file_factory import FileFactory


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
