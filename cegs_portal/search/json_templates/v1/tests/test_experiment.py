import pytest

from cegs_portal.search.json_templates.v1.experiment import biosample as b_json
from cegs_portal.search.json_templates.v1.experiment import experiment as exp_json
from cegs_portal.search.json_templates.v1.experiment import experiments as exps_json
from cegs_portal.search.json_templates.v1.experiment import file as f_json
from cegs_portal.search.models import Experiment, File
from cegs_portal.search.models.experiment import Biosample
from cegs_portal.utils.pagination_types import Pageable

pytestmark = pytest.mark.django_db


def test_experiments_json(paged_experiments: Pageable[Experiment]):
    result = {
        "object_list": [
            {
                "accession_id": e.accession_id,
                "name": e.name,
                "description": e.description,
                "biosamples": [b_json(b) for b in e.biosamples.all()],
            }
            for e in paged_experiments.object_list
        ],
        "page": paged_experiments.number,
        "has_next_page": paged_experiments.has_next(),
        "has_prev_page": paged_experiments.has_previous(),
        "num_pages": paged_experiments.paginator.num_pages,
    }

    assert exps_json(paged_experiments) == result


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
