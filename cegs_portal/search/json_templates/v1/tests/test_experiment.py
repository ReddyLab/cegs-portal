from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.experiment import biosample as b_json
from cegs_portal.search.json_templates.v1.experiment import data_file as df_json
from cegs_portal.search.json_templates.v1.experiment import experiment as exp_json
from cegs_portal.search.json_templates.v1.experiment import experiments as exps_json
from cegs_portal.search.json_templates.v1.experiment import other_file as of_json
from cegs_portal.search.models import Experiment, ExperimentDataFile, File
from cegs_portal.search.models.experiment import Biosample

pytestmark = pytest.mark.django_db


def test_experiments_json(experiments: Iterable[Experiment]):
    for experiment in experiments:
        experi_cell_lines: list[str] = []
        experi_tissue_types: list[str] = []
        for bios in experiment.biosamples.all():
            experi_cell_lines.append(bios.cell_line_name)
            experi_tissue_types.append(bios.cell_line.tissue_type_name)

        setattr(experiment, "cell_lines", experi_cell_lines)
        setattr(experiment, "tissue_types", experi_tissue_types)

    result = [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "biosamples": [b_json(b) for b in e.biosamples.all()],
        }
        for e in experiments
    ]

    assert exps_json(experiments) == result


def test_experiment_json(experiment: Experiment):
    experi_cell_lines: list[str] = []
    for bios in experiment.biosamples.all():
        experi_cell_lines.append(bios.cell_line_name)

    setattr(experiment, "cell_lines", ", ".join(experi_cell_lines))

    assert exp_json(experiment) == {
        "id": experiment.id,
        "name": experiment.name,
        "description": experiment.description,
        "assay": experiment.experiment_type,
        "biosamples": [b_json(b) for b in experiment.biosamples.all()],
        "data_files": [df_json(file) for file in experiment.data_files.all()],
        "other_files": [of_json(file) for file in experiment.other_files.all()],
    }


def test_biosamples(biosample: Biosample):
    assert b_json(biosample) == {
        "name": biosample.name,
        "cell_line": biosample.cell_line_name,
    }


def test_data_files(data_file: ExperimentDataFile):
    assert df_json(data_file) == {
        "filename": data_file.filename,
        "description": data_file.description,
        "assembly": f"{data_file.ref_genome}.{data_file.ref_genome_patch or '0'}",
    }


def test_other_files(other_file: File):
    assert of_json(other_file) == {
        "filename": other_file.filename,
        "description": other_file.description,
        "url": other_file.url,
    }
