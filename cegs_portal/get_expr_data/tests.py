import json
from io import StringIO
from time import sleep

import pytest

from cegs_portal.get_expr_data.view_models import (
    ReoDataSource,
    gen_output_filename,
    output_experiment_data_list,
    parse_source_locs,
    parse_target_info,
    retrieve_experiment_data,
    validate_expr,
    validate_filename,
    write_experiment_data_csv,
)
from cegs_portal.search.conftest import SearchClient

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "accession_id,valid",
    [
        ("DCPEXPR00000002", True),
        ("DCPEXPRAAAAAAAA", True),
        ("DCPEXP00000002", False),
        ("DCPEXPR0000000F", True),
        ("DCPEXPR0000000G", False),
    ],
)
def test_validate_expr(accession_id, valid):
    assert validate_expr(accession_id) == valid


@pytest.mark.parametrize(
    "filename,valid",
    [
        ("DCPEXPR00000002.DCPEXPR00000003.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv", True),
        ("DCPEXPR00000002.DCPEXPR00000003.981152cc-67da-403f-97e1-b2ff5c1051f8", False),
        ("DCPEXPR00000002.DCPEXPR00000003.981152cc-67da-403f-97e1-b2ff5c1051f.tsv", False),
        ("DCPEXPR00000002.DCPEXPR0000000K.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv", False),
        ("DCPEXPR0000000K.DCPEXPR00000003.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv", False),
    ],
)
def test_validate_filename(filename, valid):
    assert validate_filename(filename) == valid


@pytest.mark.parametrize(
    "expr_accession_ids,an_accession_ids,valid",
    [
        (["DCPEXPR00000002"], [], True),
        (["DCPEXPR00000002", "DCPEXPR00000003"], [], True),
        (["DCPEXPR0000000K"], [], False),
        (["DCPEXPR00000002", "DCPXPR00000003"], [], False),
        ([], ["DCPAN00000002"], True),
        ([], ["DCPAN00000002", "DCPAN00000003"], True),
        ([], ["DCPAN0000000K"], False),
        ([], ["DCPAN00000002", "DCPN00000003"], False),
        (["DCPEXPR00000002"], ["DCPAN00000002"], True),
        (["DCPEXPR00000002", "DCPEXPR00000003"], ["DCPAN00000002", "DCPAN00000003"], True),
        (["DCPEXPR0000000K"], ["DCPAN0000000K"], False),
        (["DCPEXPR00000002", "DCPXPR00000003"], ["DCPAN00000002", "DCPN00000003"], False),
    ],
)
def test_gen_output_filename(expr_accession_ids, an_accession_ids, valid):
    assert validate_filename(gen_output_filename(expr_accession_ids, an_accession_ids)) == valid


@pytest.mark.parametrize(
    "source_locs,result",
    [
        ('{"(,)"}', []),
        (r'{"(chr1,\"[11,1001)\")"}', ["chr1:11-1001"]),
        (r'{"(chr1,\"[11,1001)\")","(chr2,\"[22223,33334)\")"}', ["chr1:11-1001", "chr2:22223-33334"]),
    ],
)
def test_parse_source_locs(source_locs, result):
    assert parse_source_locs(source_locs) == result


@pytest.mark.parametrize(
    "target_info,result",
    [
        ('{"(,,,)"}', []),
        (r'{"(chr1,\"[35001,40001)\",GWSR-1,ENSG20717717659)"}', ["GWSR-1:ENSG20717717659"]),
        (
            r'{"(chr1,\"[35001,40001)\",GWSR-1,ENSG20717717659)","(chr1,\"[35000,40000)\",PKND-1,ENSG20717717659)"}',
            ["GWSR-1:ENSG20717717659", "PKND-1:ENSG20717717659"],
        ),
    ],
)
def test_parse_target_info(target_info, result):
    assert parse_target_info(target_info) == result


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_both_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], ReoDataSource.BOTH
    )

    assert len(result) == 3


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_source_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], ReoDataSource.SOURCES
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_target_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], ReoDataSource.TARGETS
    )

    assert len(result) == 2


def test_list_experiment_data(reg_effects):
    _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    results = output_experiment_data_list(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], ReoDataSource.BOTH
    )

    assert results == [
        {
            "source locs": [],
            "targets": [{"gene sym": "LNLC-1", "gene id": "ENSG01124619313"}],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR00000002",
            "analysis id": analysis_accession_id,
        },
        {
            "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
            "targets": [],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR00000002",
            "analysis id": analysis_accession_id,
        },
        {
            "source locs": ["chr1:11-1001", "chr2:22223-33334"],
            "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR00000002",
            "analysis id": analysis_accession_id,
        },
    ]


def test_list_analysis_data(reg_effects):
    _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    results = output_experiment_data_list(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], [], [analysis_accession_id], ReoDataSource.BOTH
    )

    assert results == [
        {
            "source locs": [],
            "targets": [{"gene sym": "LNLC-1", "gene id": "ENSG01124619313"}],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR00000002",
            "analysis id": analysis_accession_id,
        },
        {
            "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
            "targets": [],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR00000002",
            "analysis id": analysis_accession_id,
        },
        {
            "source locs": ["chr1:11-1001", "chr2:22223-33334"],
            "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR00000002",
            "analysis id": analysis_accession_id,
        },
    ]


def test_location_experiment_data(reg_effects, login_client: SearchClient):
    _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    response = login_client.get("/exp_data/location?region=chr1:1-100000&expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 200
    json_content = json.loads(response.content)
    print(json_content)
    assert json_content == {
        "experiment data": [
            {
                "source locs": [],
                "targets": [{"gene sym": "LNLC-1", "gene id": "ENSG01124619313"}],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR00000002",
                "analysis id": analysis_accession_id,
            },
            {
                "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
                "targets": [],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR00000002",
                "analysis id": analysis_accession_id,
            },
            {
                "source locs": ["chr1:11-1001", "chr2:22223-33334"],
                "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR00000002",
                "analysis id": analysis_accession_id,
            },
        ]
    }


def test_location_analysis_data(reg_effects, login_client: SearchClient):
    _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    response = login_client.get(f"/exp_data/location?region=chr1:1-100000&an={analysis_accession_id}&datasource=both")
    assert response.status_code == 200
    json_content = json.loads(response.content)
    print(json_content)
    assert json_content == {
        "experiment data": [
            {
                "source locs": [],
                "targets": [{"gene sym": "LNLC-1", "gene id": "ENSG01124619313"}],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR00000002",
                "analysis id": analysis_accession_id,
            },
            {
                "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
                "targets": [],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR00000002",
                "analysis id": analysis_accession_id,
            },
            {
                "source locs": ["chr1:11-1001", "chr2:22223-33334"],
                "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR00000002",
                "analysis id": analysis_accession_id,
            },
        ]
    }


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_invalid_region(login_client: SearchClient):
    response = login_client.get("/exp_data/location?region=ch1:1-100000&expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_no_region(login_client: SearchClient):
    response = login_client.get("/exp_data/location?expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_oversize_region(login_client: SearchClient):
    response = login_client.get("/exp_data/location?region=chr1:1-1000000&expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_backwards_region(login_client: SearchClient):
    response = login_client.get("/exp_data/location?region=chr1:10000-10&expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 400


def test_write_experiment_data(reg_effects):
    _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    experiment_data = list(
        retrieve_experiment_data(
            [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], ReoDataSource.BOTH
        )
    )
    experiment_data.sort()
    output_file = StringIO()
    write_experiment_data_csv(experiment_data, output_file)
    assert (
        output_file.getvalue()
        == f"Source Locs\tTarget Info\tp-value\tAdjusted p-value\tEffect Size\tExpr Accession Id\tAnalysis Accession Id\n"  # noqa: E501
        f"\tLNLC-1:ENSG01124619313\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR00000002\t{analysis_accession_id}\n"  # noqa: E501
        f"chr1:10-1000,chr1:20000-111000,chr2:22222-33333\t\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR00000002\t{analysis_accession_id}\n"  # noqa: E501
        f"chr1:11-1001,chr2:22223-33334\tXUEQ-1:ENSG01124619313\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR00000002\t{analysis_accession_id}\n"  # noqa: E501
    )


def test_write_analysis_data(reg_effects):
    _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    experiment_data = list(
        retrieve_experiment_data(
            [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], [], [analysis_accession_id], ReoDataSource.BOTH
        )
    )
    experiment_data.sort()
    output_file = StringIO()
    write_experiment_data_csv(experiment_data, output_file)
    assert (
        output_file.getvalue()
        == f"Source Locs\tTarget Info\tp-value\tAdjusted p-value\tEffect Size\tExpr Accession Id\tAnalysis Accession Id\n"  # noqa: E501
        f"\tLNLC-1:ENSG01124619313\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR00000002\t{analysis_accession_id}\n"  # noqa: E501
        f"chr1:10-1000,chr1:20000-111000,chr2:22222-33333\t\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR00000002\t{analysis_accession_id}\n"  # noqa: E501
        f"chr1:11-1001,chr2:22223-33334\tXUEQ-1:ENSG01124619313\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR00000002\t{analysis_accession_id}\n"  # noqa: E501
    )


@pytest.mark.usefixtures("reg_effects")
def test_request_experiment_data(login_client: SearchClient):
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = login_client.post(
        "/exp_data/request?expr=DCPEXPR00000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    )
    assert response.status_code == 200
    sleep(0.1)
    json_content = json.loads(response.content)
    loc_response = login_client.get(json_content["file location"])
    assert loc_response.status_code == 200

    prog_response = login_client.get(json_content["file progress"])
    assert prog_response.status_code == 200


def test_download_experiment_data_success(login_client: SearchClient):
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = login_client.post(
        "/exp_data/request?expr=DCPEXPR00000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    )
    assert response.status_code == 200
    sleep(0.1)
    json_content = json.loads(response.content)
    loc_response = login_client.get(json_content["file location"])
    assert loc_response.status_code == 200
    content = StringIO()
    for data in loc_response.streaming_content:
        content.write(data.decode())
    assert len(content.getvalue()) > 0


def test_download_experiment_data_fail(login_client: SearchClient):
    response = login_client.get("/exp_data/file/DCPEXPR00000002.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv")
    assert response.status_code == 404


def test_download_experiment_data_invalid_filename(login_client: SearchClient):
    response = login_client.get("/exp_data/file/DCPEXPR0000000K.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv")
    assert response.status_code == 400
