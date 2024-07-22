from typing import Any, Optional

from cegs_portal.search.models import Biosample, Experiment, File


def experiments(experiments_data: tuple[Any, Any], options: Optional[dict[str, Any]] = None):
    experiments_obj, _ = experiments_data
    return {
        "experiments": [
            {
                "accession_id": e.accession_id,
                "name": e.name,
                "description": e.description if e.description is not None else "",
                "biosamples": [biosample(b) for b in e.biosamples.all()],
            }
            for e in experiments_obj
        ],
    }


def experiment(experiment_obj: Experiment, options: Optional[dict[str, Any]] = None):
    result = {
        "accession_id": experiment_obj.accession_id,
        "name": experiment_obj.name,
        "description": experiment_obj.description if experiment_obj.description is not None else "",
        "assay": experiment_obj.experiment_type,
        "biosamples": [biosample(b) for b in experiment_obj.biosamples.all()],
        "files": [file(f) for f in experiment_obj.files.all()],
    }

    return result


def biosample(biosample_obj: Biosample):
    return {
        "name": biosample_obj.name,
        "cell_line": biosample_obj.cell_line_name,
    }


def file(file_obj: File):
    result = {
        "filename": file_obj.filename,
        "description": file_obj.description,
        "url": file_obj.url,
        "size": file_obj.size,
        "category": file_obj.category,
    }

    return result
