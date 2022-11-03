import json

import pytest
from django.test import Client

from cegs_portal.search.models import RegulatoryEffectObservation

pytestmark = pytest.mark.django_db


def test_experiment_json(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(f"/search/regeffect/{reg_effect.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["accession_id"] == reg_effect.accession_id
    assert json_content["direction"] == reg_effect.direction
    assert json_content["effect_size"] == reg_effect.effect_size
    assert json_content["significance"] == reg_effect.significance


def test_experiment_html(client: Client, reg_effect: RegulatoryEffectObservation):
    response = client.get(f"/search/regeffect/{reg_effect.accession_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200
