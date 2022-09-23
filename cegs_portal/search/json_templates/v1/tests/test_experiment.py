from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.experiment import data_file as df_json
from cegs_portal.search.json_templates.v1.experiment import experiment as exp_json
from cegs_portal.search.json_templates.v1.experiment import experiments as exps_json
from cegs_portal.search.json_templates.v1.experiment import other_file as of_json
from cegs_portal.search.models import Experiment, ExperimentDataFile, File
from cegs_portal.search.models.experiment import CellLine, TissueType

pytestmark = pytest.mark.django_db


def test_experiments_json(experiments: Iterable[Experiment]):
    for experiment in experiments:
        experi_cell_lines: list[CellLine] = []
        experi_tissue_types: list[TissueType] = []
        for f in experiment.data_files.all():
            experi_cell_lines.extend(f.cell_lines.all())
            experi_tissue_types.extend(f.tissue_types.all())

        setattr(experiment, "cell_lines", experi_cell_lines)
        setattr(experiment, "tissue_types", experi_tissue_types)

    result = [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "cell_lines": e.cell_lines,  # type: ignore[attr-defined]
            "tissue_types": e.tissue_types,  # type: ignore[attr-defined]
        }
        for e in experiments
    ]

    assert exps_json(experiments) == result


def test_experiment_json(experiment: Experiment):
    experi_cell_lines: list[str] = []
    for f in experiment.data_files.all():
        experi_cell_lines.append(f.cell_line)

    setattr(experiment, "cell_lines", ", ".join(experi_cell_lines))

    assert exp_json(experiment) == {
        "id": experiment.id,
        "name": experiment.name,
        "description": experiment.description,
        "assay": experiment.experiment_type,
        "cell_lines": ", ".join(experi_cell_lines),
        "data_files": [df_json(file) for file in experiment.data_files.all()],
        "other_files": [of_json(file) for file in experiment.other_files.all()],
    }


def test_data_files(data_file: ExperimentDataFile):
    assert df_json(data_file) == {
        "filename": data_file.filename,
        "description": data_file.description,
        "cell_lines": [str(line) for line in data_file.cell_lines.all()],
        "tissue_types": [str(tt) for tt in data_file.tissue_types.all()],
        "assembly": f"{data_file.ref_genome}.{data_file.ref_genome_patch or '0'}",
    }


def test_other_files(other_file: File):
    assert of_json(other_file) == {
        "filename": other_file.filename,
        "description": other_file.description,
        "url": other_file.url,
    }
