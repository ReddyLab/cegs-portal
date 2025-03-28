from typing import Any

import pytest

from cegs_portal.search.json_templates.v1.experiment import biosample as b_json
from cegs_portal.search.json_templates.v1.experiment import experiment as exp_json
from cegs_portal.search.json_templates.v1.experiment import experiments as exps_json
from cegs_portal.search.json_templates.v1.experiment import file as f_json
from cegs_portal.search.json_templates.v1.experiment_collection import (
    experiment_collection,
)
from cegs_portal.search.models import Experiment, File
from cegs_portal.search.models.experiment import Biosample

pytestmark = pytest.mark.django_db


def test_experiments_json(experiment_list_data: tuple[Any, Any, Any, Any, Any, Any]):
    experiments_obj, igvf_obj, collections_obj, _, _, _ = experiment_list_data
    collections = sorted(collections_obj, key=lambda x: x.accession_id)
    result = {
        "experiments": [
            {
                "accession_id": e.accession_id,
                "name": e.name,
                "description": e.description if e.description is not None else "",
                "biosamples": [b_json(b) for b in e.biosamples.all()],
                "genome_assembly": e.default_analysis.genome_assembly,
            }
            for e in experiments_obj
        ],
        "igvf_experiments": [
            {
                "accession_id": e.accession_id,
                "name": e.name,
                "description": e.description if e.description is not None else "",
                "biosamples": [b_json(b) for b in e.biosamples.all()],
                "genome_assembly": e.default_analysis.genome_assembly,
            }
            for e in igvf_obj
        ],
        "experiment_collections": [experiment_collection((c, c.experiments.all())) for c in collections],
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
        "description": experiment.description if experiment.description is not None else "",
        "assay": experiment.experiment_type,
        "biosamples": [b_json(b) for b in experiment.biosamples.all()],
        "files": [f_json(file) for file in experiment.files.all()],
        "attribution": {
            "pi": experiment.attribution.pi,
            "institution": experiment.attribution.institution,
            "experimentalist": experiment.attribution.experimentalist,
            "project": experiment.attribution.project,
            "datasource_url": experiment.attribution.datasource_url,
            "lab_url": experiment.attribution.lab_url,
        },
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
