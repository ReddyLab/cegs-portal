import json

import pytest
from django.test import Client

from cegs_portal.search.models import DNAFeature

pytestmark = pytest.mark.django_db


def test_source_reg_effects_list_json(client: Client, source_reg_effects):
    source = source_reg_effects["source"]
    effects = sorted(source_reg_effects["effects"], key=lambda x: x.accession_id)
    response = client.get(f"/search/regeffect/source/{source.accession_id}?accept=application/json")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == len(effects)

    for json_reo, reo in zip(json_content["object_list"], effects):
        assert json_reo["accession_id"] == reo.accession_id
        assert json_reo["effect_size"] == reo.effect_size
        assert json_reo["direction"] == reo.direction
        assert json_reo["significance"] == reo.significance


def test_source_reg_effects_list_page_json(client: Client, source_reg_effects):
    source = source_reg_effects["source"]
    effects = sorted(source_reg_effects["effects"], key=lambda x: x.accession_id)
    response = client.get(f"/search/regeffect/source/{source.accession_id}?accept=application/json&page=1&per_page=1")

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert len(json_content["object_list"]) == 1
    assert json_content["num_pages"] == 3

    json_reo = json_content["object_list"][0]
    reo = effects[0]

    assert json_reo["accession_id"] == reo.accession_id
    assert json_reo["effect_size"] == reo.effect_size
    assert json_reo["direction"] == reo.direction
    assert json_reo["significance"] == reo.significance


def test_source_regeffect_html(client: Client, feature: DNAFeature):
    response = client.get(f"/search/regeffect/source/{feature.accession_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200