from typing import Any, Optional

from cegs_portal.search.models import Biosample, Experiment, File
from cegs_portal.utils.pagination_types import Pageable


def experiments(experiments_obj: Pageable[Experiment], options: Optional[dict[str, Any]] = None):
    return {
        "object_list": [
            {
                "accession_id": e.accession_id,
                "name": e.name,
                "description": e.description,
                "biosamples": [biosample(b) for b in e.biosamples.all()],
            }
            for e in experiments_obj.object_list
        ],
        "page": experiments_obj.number,
        "has_next_page": experiments_obj.has_next(),
        "has_prev_page": experiments_obj.has_previous(),
        "num_pages": experiments_obj.paginator.num_pages,
    }


def experiment(experiment_obj: Experiment, options: Optional[dict[str, Any]] = None):
    result = {
        "accession_id": experiment_obj.accession_id,
        "name": experiment_obj.name,
        "description": experiment_obj.description,
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

    if file_obj.data_file_info is not None:
        result["assembly"] = f"{file_obj.data_file_info.ref_genome}.{file_obj.data_file_info.ref_genome_patch or '0'}"
        result["p_val_threshold"] = file_obj.data_file_info.p_value_threshold
        result["significance_measure"] = file_obj.data_file_info.significance_measure

    return result
