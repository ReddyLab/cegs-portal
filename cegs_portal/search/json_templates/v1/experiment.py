from typing import Iterable

from cegs_portal.search.models import Experiment, ExperimentDataFile, File


def experiments(experiments_obj: Iterable[Experiment]):
    results = [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "cell_lines": None,
            "tissue_types": None,
        }
        for e in experiments_obj
    ]

    for e, result in zip(experiments_obj, results):
        if hasattr(e, "cell_lines"):
            result["cell_lines"] = [line for line in e.cell_lines]  # type: ignore[attr-defined]

        if hasattr(e, "tissue_types"):
            result["tissue_types"] = [tt for tt in e.tissue_types]  # type: ignore[attr-defined]

    return results


def experiment(experiment_obj: Experiment, json_format: str = None):
    result = {
        "id": experiment_obj.id,
        "name": experiment_obj.name,
        "description": experiment_obj.description,
        "assay": experiment_obj.experiment_type,
        "cell_lines": None,
        "tissue_types": None,
        "assemblies": None,
        "data_files": [data_file(f) for f in experiment_obj.data_files.all()],
        "other_files": [other_file(f) for f in experiment_obj.other_files.all()],
    }

    if hasattr(experiment_obj, "cell_lines"):
        result["cell_lines"] = [str(line) for line in experiment_obj.cell_lines]  # type: ignore[attr-defined]

    if hasattr(experiment_obj, "tissue_types"):
        result["tissue_types"] = [str(tt) for tt in experiment_obj.tissue_types]  # type: ignore[attr-defined]

    if hasattr(experiment_obj, "assemblies"):
        result["assemblies"] = list(experiment_obj.assemblies)  # type: ignore[attr-defined]

    return result


def data_file(data_file_obj: ExperimentDataFile):
    return {
        "filename": data_file_obj.filename,
        "description": data_file_obj.description,
        "cell_lines": [str(line) for line in data_file_obj.cell_lines.all()],
        "tissue_types": [str(tt) for tt in data_file_obj.tissue_types.all()],
        "assembly": f"{data_file_obj.ref_genome}.{data_file_obj.ref_genome_patch or '0'}",
    }


def other_file(file_obj: File):
    return {
        "filename": file_obj.filename,
        "description": file_obj.description,
        "url": file_obj.url,
    }
