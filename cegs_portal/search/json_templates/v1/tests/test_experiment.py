from typing import Any

import pytest

from cegs_portal.search.json_templates.v1.experiment import biosample as b_json
from cegs_portal.search.json_templates.v1.experiment import experiment as exp_json
from cegs_portal.search.json_templates.v1.experiment import experiments as exps_json
from cegs_portal.search.json_templates.v1.experiment import file as f_json
from cegs_portal.search.models import Experiment, File
from cegs_portal.search.models.experiment import Biosample

pytestmark = pytest.mark.django_db


def test_experiments_json(experiment_list_data: tuple[Any, Any]):
    experiments_obj, _ = experiment_list_data
    result = {
        "experiments": [
            {
                "accession_id": e.accession_id,
                "name": e.name,
                "description": e.description,
                "biosamples": [b_json(b) for b in e.biosamples.all()],
            }
            for e in experiments_obj
        ]
    }

    assert exps_json(experiment_list_data) == result


def test_experiment_json(experiment: Experiment):
    experi_cell_lines: list[str] = []
    for bios in experiment.biosamples.all():
        experi_cell_lines.append(bios.cell_line_name)

    setattr(experiment, "cell_lines", ", ".join(experi_cell_lines))

    assert exp_json(experiment) == {
        "accession_id": experiment.accession_id,
        "name": experiment.name,
        "description": experiment.description,
        "assay": experiment.experiment_type,
        "biosamples": [b_json(b) for b in experiment.biosamples.all()],
        "files": [f_json(file) for file in experiment.files.all()],
    }


def test_biosamples(biosample: Biosample):
    assert b_json(biosample) == {
        "name": biosample.name,
        "cell_line": biosample.cell_line_name,
    }


def test_file(file: File):
    assert f_json(file) == {
        "filename": file.filename,
        "description": file.description,
        "url": file.url,
        "size": file.size,
        "category": file.category,
    }
