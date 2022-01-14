from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.experiment import data_file as df_json
from cegs_portal.search.json_templates.v1.experiment import experiment as exp_json
from cegs_portal.search.json_templates.v1.experiment import experiments as exps_json
from cegs_portal.search.json_templates.v1.experiment import other_file as of_json
from cegs_portal.search.models import Experiment, ExperimentDataFile, File

pytestmark = pytest.mark.django_db


def test_experiments_json(experiments: Iterable[Experiment]):
    for experiment in experiments:
        experi_cell_lines = []
        experi_tissue_types = []
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
            "cell_lines": e.cell_lines,
            "tissue_types": e.tissue_types,
        }
        for e in experiments
    ]

    assert exps_json(experiments) == result


def test_experiment_json(experiment: Experiment):
    experi_cell_lines = []
    experi_tissue_types = []
    experi_assemblies = []
    for f in experiment.data_files.all():
        experi_cell_lines.extend(f.cell_lines.all())
        experi_tissue_types.extend(f.tissue_types.all())
        experi_assemblies.append(f"{f.ref_genome}.{f.ref_genome_patch or '0'}")

    setattr(experiment, "cell_lines", experi_cell_lines)
    setattr(experiment, "tissue_types", experi_tissue_types)
    setattr(experiment, "assemblies", experi_assemblies)

    assert exp_json(experiment) == {
        "id": experiment.id,
        "name": experiment.name,
        "description": experiment.description,
        "assay": experiment.experiment_type,
        "cell_lines": [str(line) for line in experi_cell_lines],
        "tissue_types": [str(tt) for tt in experi_tissue_types],
        "assemblies": [str(a) for a in experi_assemblies],
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
