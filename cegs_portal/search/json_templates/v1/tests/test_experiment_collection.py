import pytest

from cegs_portal.search.json_templates.v1.experiment_collection import (
    experiment_collection as e_coll,
)
from cegs_portal.search.models import ExperimentCollection

pytestmark = pytest.mark.django_db


def test_experiment_collection_json(experiment_collection: ExperimentCollection):
    experiments = experiment_collection.experiments.all()
    result = {
        "accession_id": experiment_collection.accession_id,
        "name": experiment_collection.name,
        "description": experiment_collection.description,
        "experiments": [
            {
                "accession_id": e.accession_id,
                "name": e.name,
            }
            for e in experiments
        ],
    }

    assert e_coll((experiment_collection, experiments)) == result
