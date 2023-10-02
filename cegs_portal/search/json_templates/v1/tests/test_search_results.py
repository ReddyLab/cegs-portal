import pytest

from cegs_portal.search.json_templates.v1.dna_features import features
from cegs_portal.search.json_templates.v1.search_results import (
    SearchResults,
    parse_source_locs_json,
    parse_source_target_data_json,
    parse_target_info_json,
)
from cegs_portal.search.json_templates.v1.search_results import (
    search_results as sr_json,
)

pytestmark = pytest.mark.django_db


def test_search_results(search_results: SearchResults):
    assert sr_json(search_results) == {
        "location": {
            "assembly": search_results["assembly"],
            "chromosome": search_results["location"].chromo,
            "start": search_results["location"].range.lower,
            "end": search_results["location"].range.upper,
        },
        "features": features(search_results["features"]),
        "sig_reg_effects": [
            (
                ("DCPEXPR00000001", "DCPAN00000001"),
                [
                    {
                        "source_locs": [("chr6", 31577822, 31578136, "DCPDHS00000001")],
                        "target_info": [("ZBTB12", "ENSG00000204366")],
                        "reo_accession_id": "DCPREO000339D6",
                        "effect_size": 0.010958133,
                        "p_value": 0.00000184,
                        "sig": 0.000547435,
                        "expr_accession_id": "DCPEXPR00000002",
                        "expr_name": "Tyler scCERES Experiment 2021",
                        "analysis_accession_id": "DCPAN00000002",
                    },
                    {
                        "source_locs": [("chr6", 32182864, 32183339, "DCPDHS00000002")],
                        "target_info": [("SLC44A4", "ENSG00000204385")],
                        "reo_accession_id": "DCPREO00033A96",
                        "effect_size": -0.005418836,
                        "p_value": 0.001948499,
                        "sig": 0.004785014,
                        "expr_accession_id": "DCPEXPR00000002",
                        "expr_name": "Tyler scCERES Experiment 2021",
                        "analysis_accession_id": "DCPAN00000002",
                    },
                    {
                        "source_locs": [("chr13", 40666345, 40666366, "DCPDHS00000003")],
                        "target_info": [("SNHG32", "ENSG00000204387")],
                        "reo_accession_id": "DCPREO004F45A1",
                        "effect_size": -1.2,
                        "p_value": 0.005,
                        "sig": 0.05,
                        "expr_accession_id": "DCPEXPR00000009",
                        "expr_name": "Test Name",
                        "analysis_accession_id": "DCPAN00000008",
                    },
                ],
            )
        ],
        "facets": [
            {"name": f.name, "description": f.description, "values": [value.value for value in f.values.all()]}
            for f in search_results["facets"].all()
        ],
    }

    assert sr_json(search_results, {"json_format": "genoverse"}) == {
        "location": {
            "assembly": search_results["assembly"],
            "chromosome": search_results["location"].chromo,
            "start": search_results["location"].range.lower,
            "end": search_results["location"].range.upper,
        },
        "features": features(search_results["features"], {"json_format": "genoverse"}),
        "sig_reg_effects": [
            (
                ("DCPEXPR00000001", "DCPAN00000001"),
                [
                    {
                        "source_locs": [("chr6", 31577822, 31578136, "DCPDHS00000001")],
                        "target_info": [("ZBTB12", "ENSG00000204366")],
                        "reo_accession_id": "DCPREO000339D6",
                        "effect_size": 0.010958133,
                        "p_value": 0.00000184,
                        "sig": 0.000547435,
                        "expr_accession_id": "DCPEXPR00000002",
                        "expr_name": "Tyler scCERES Experiment 2021",
                        "analysis_accession_id": "DCPAN00000002",
                    },
                    {
                        "source_locs": [("chr6", 32182864, 32183339, "DCPDHS00000002")],
                        "target_info": [("SLC44A4", "ENSG00000204385")],
                        "reo_accession_id": "DCPREO00033A96",
                        "effect_size": -0.005418836,
                        "p_value": 0.001948499,
                        "sig": 0.004785014,
                        "expr_accession_id": "DCPEXPR00000002",
                        "expr_name": "Tyler scCERES Experiment 2021",
                        "analysis_accession_id": "DCPAN00000002",
                    },
                    {
                        "source_locs": [("chr13", 40666345, 40666366, "DCPDHS00000003")],
                        "target_info": [("SNHG32", "ENSG00000204387")],
                        "reo_accession_id": "DCPREO004F45A1",
                        "effect_size": -1.2,
                        "p_value": 0.005,
                        "sig": 0.05,
                        "expr_accession_id": "DCPEXPR00000009",
                        "expr_name": "Test Name",
                        "analysis_accession_id": "DCPAN00000008",
                    },
                ],
            )
        ],
        "facets": [
            {"name": f.name, "description": f.description, "values": [value.value for value in f.values.all()]}
            for f in search_results["facets"].all()
        ],
    }


def test_parse_source_locs_json():
    assert parse_source_locs_json('{(chr1,\\"[1,2)\\",DCPDHS00000001)}') == [("chr1", 1, 2, "DCPDHS00000001")]
    assert parse_source_locs_json('{(chr1,\\"[1,2)\\",DCPDHS00000001),(chr2,\\"[2,4)\\",DCPDHS00000002)}') == [
        ("chr1", 1, 2, "DCPDHS00000001"),
        ("chr2", 2, 4, "DCPDHS00000002"),
    ]


def test_parse_source_target_data_json():
    test_data = {
        "target_info": '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}',
        "source_locs": '{(chr1,\\"[1,2)\\",DCPDHS00000001)}',
        "asdf": 1234,
    }
    assert parse_source_target_data_json(test_data) == {
        "target_info": [("ZBTB12", "ENSG00000204366")],
        "source_locs": [("chr1", 1, 2, "DCPDHS00000001")],
        "asdf": 1234,
    }


def test_parse_target_info_json():
    assert parse_target_info_json('{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}') == [
        ("ZBTB12", "ENSG00000204366")
    ]
    assert parse_target_info_json(
        '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)","(chr6,\\"[8386234,2389234)\\",HLA-A,ENSG00000204367)"}'  # noqa: E501
    ) == [("ZBTB12", "ENSG00000204366"), ("HLA-A", "ENSG00000204367")]
