from typing import Any, Optional

from cegs_portal.search.models import Experiment, ExperimentCollection


def experiment_collection(
    data: tuple[ExperimentCollection, list[Experiment]], options: Optional[dict[str, Any]] = None
):
    collection, experiments = data
    result = {
        "accession_id": collection.accession_id,
        "name": collection.name,
        "description": collection.description if collection.description is not None else "",
        "experiments": [{"accession_id": expr.accession_id, "name": expr.name} for expr in experiments],
    }

    return result
