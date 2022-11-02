from typing import Any, Optional

from cegs_portal.search.models import Experiment, ExperimentDataFile, File
from cegs_portal.utils.pagination_types import Pageable


def experiments(experiments_obj: Pageable[Experiment], options: Optional[dict[str, Any]] = None):
    results = [
        {
            "accession_id": e.accession_id,
            "name": e.name,
            "description": e.description,
            "biosamples": [biosample(b) for b in e.biosamples.all()],
        }
        for e in experiments_obj.object_list
    ]

    return results


def experiment(experiment_obj: Experiment, options: Optional[dict[str, Any]] = None):
    result = {
        "accession_id": experiment_obj.accession_id,
        "name": experiment_obj.name,
        "description": experiment_obj.description,
        "assay": experiment_obj.experiment_type,
        "biosamples": [biosample(b) for b in experiment_obj.biosamples.all()],
        "data_files": [data_file(f) for f in experiment_obj.data_files.all()],
        "other_files": [other_file(f) for f in experiment_obj.other_files.all()],
    }

    return result


def biosample(biosample_obj: ExperimentDataFile):
    return {
        "name": biosample_obj.name,
        "cell_line": biosample_obj.cell_line_name,
    }


def data_file(data_file_obj: ExperimentDataFile):
    return {
        "filename": data_file_obj.filename,
        "description": data_file_obj.description,
        "assembly": f"{data_file_obj.ref_genome}.{data_file_obj.ref_genome_patch or '0'}",
    }


def other_file(file_obj: File):
    return {
        "filename": file_obj.filename,
        "description": file_obj.description,
        "url": file_obj.url,
    }
