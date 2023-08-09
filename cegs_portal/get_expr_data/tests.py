import json
from io import StringIO
from time import sleep

import pytest

from cegs_portal.conftest import SearchClient
from cegs_portal.get_expr_data.view_models import (
    Facets,
    ReoDataSource,
    gen_output_filename,
    output_experiment_data_list,
    parse_source_locs,
    parse_target_info,
    retrieve_experiment_data,
    sig_reo_loc_search,
    validate_expr,
    validate_filename,
    write_experiment_data_csv,
)

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
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], Facets(), ReoDataSource.BOTH
    )

    assert len(result) == 3


@pytest.mark.usefixtures("private_reg_effects")
def test_retrieve_private_experiment_data_no_exprs():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], Facets(), ReoDataSource.BOTH
    )

    assert len(result) == 0


@pytest.mark.usefixtures("private_reg_effects")
def test_retrieve_private_experiment_data_with_expr():
    result = retrieve_experiment_data(
        ["DCPEXPR00000002"],
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)],
        ["DCPEXPR00000002"],
        [],
        Facets(),
        ReoDataSource.BOTH,
    )

    assert len(result) == 3


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_source_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], Facets(), ReoDataSource.SOURCES
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_target_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], Facets(), ReoDataSource.TARGETS
    )

    assert len(result) == 2


@pytest.mark.parametrize(
    "cat_facets,effect_size,sig,result_count",
    [
        ([], (-10, 0), (None, None), 3),
        ([], (0, 10), (None, None), 0),
        ([], (None, None), (0.0, 0.00004), 0),
        ([], (None, None), (0.0, 0.005), 3),
        ([], (-10, 0), (0.0, 0.005), 3),
        ([], (0, 10), (0.0, 0.005), 0),
        ([], (-10, 0), (0.0, 0.00004), 0),
        ([], (0, 10), (0.0, 0.00004), 0),
    ],
)
@pytest.mark.usefixtures("reg_effects")
def test_retrieve_num_facet_experiment_data(cat_facets, effect_size, sig, result_count):
    facets = Facets(categorical_facets=cat_facets, effect_size_range=effect_size, sig_range=sig)
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == result_count


def test_retrieve_cat_facet_experiment_data(reg_effects):
    _, _, _, x, y, z, _ = reg_effects
    facets = Facets(categorical_facets=[])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 3

    facets = Facets(categorical_facets=[x.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 1

    facets = Facets(categorical_facets=[y.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 1

    facets = Facets(categorical_facets=[z.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 1

    facets = Facets(categorical_facets=[y.id, z.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 2

    facets = Facets(categorical_facets=[x.id, y.id, z.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 3


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_facet_source_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], Facets(), ReoDataSource.SOURCES
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_facet_target_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], Facets(), ReoDataSource.TARGETS
    )

    assert len(result) == 2


def test_list_experiment_data(reg_effects):
    _, _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    results = output_experiment_data_list(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], ReoDataSource.BOTH
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
    _, _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    results = output_experiment_data_list(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], [], [analysis_accession_id], ReoDataSource.BOTH
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
    _, _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    response = login_client.get("/exp_data/location?region=chr1:1-100000&expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 200

    json_content = json.loads(response.content)
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
    _, _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    response = login_client.get(f"/exp_data/location?region=chr1:1-100000&an={analysis_accession_id}&datasource=both")
    assert response.status_code == 200

    json_content = json.loads(response.content)
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
    response = login_client.get("/exp_data/location?region=chr1:1-10000000000&expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_backwards_region(login_client: SearchClient):
    response = login_client.get("/exp_data/location?region=chr1:10000-10&expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 400


def test_write_experiment_data(reg_effects):
    _, _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    experiment_data = list(
        retrieve_experiment_data(
            [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], [], Facets(), ReoDataSource.BOTH
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
    _, _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    experiment_data = list(
        retrieve_experiment_data(
            [],
            [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)],
            [],
            [analysis_accession_id],
            Facets(),
            ReoDataSource.BOTH,
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


def test_experiment_data_status_success(login_client: SearchClient):
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
    status_response = login_client.get(json_content["file progress"])
    assert status_response.status_code == 200
    status = json.loads(status_response.content)
    assert status["file progress"] == "ready"


def test_experiment_data_status_failure(login_client: SearchClient, public_client: SearchClient):
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
    status_response = public_client.get(json_content["file progress"])
    assert status_response.status_code == 302


def test_download_experiment_data_fail(login_client: SearchClient):
    response = login_client.get("/exp_data/file/DCPEXPR00000002.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv")
    assert response.status_code == 404


def test_download_experiment_data_invalid_filename(login_client: SearchClient):
    response = login_client.get("/exp_data/file/DCPEXPR0000000K.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_sig_reo_loc_search():
    result = sig_reo_loc_search(("chr1", 1, 1000000))

    assert len(result[0][1]) == 2


def test_private_sig_reo_loc_search(private_reg_effects):
    _, _, _, _, _, _, experiment = private_reg_effects
    result = sig_reo_loc_search(("chr1", 1, 1000000))

    assert len(result) == 0

    result = sig_reo_loc_search(("chr1", 1, 1000000), private_experiments=[experiment.accession_id])

    assert len(result[0][1]) == 2


def test_sigdata(reg_effects, login_client: SearchClient):
    effect_source, effect_target, effect_both, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id

    response = login_client.get("/exp_data/sigdata?region=chr1:1-100000")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert "significant reos" in json_content
    assert len(json_content["significant reos"]) == 1
    assert len(json_content["significant reos"][0]) == 2
    assert json_content["significant reos"][0][0] == ["DCPEXPR00000002", analysis_accession_id]
    assert len(json_content["significant reos"][0][1]) == 2
    assert {
        "source_locs": [],
        "target_info": [["LNLC-1", "ENSG01124619313"]],
        "reo_accesion_id": effect_target.accession_id,
        "effect_size": -0.0660384670056446,
        "p_value": 3.19229500470051e-06,
        "sig": 0.000427767530629869,
        "expr_accession_id": "DCPEXPR00000002",
        "expr_name": experiment.name,
        "analysis_accession_id": analysis_accession_id,
    } in json_content["significant reos"][0][1]
    assert {
        "source_locs": [["chr1", 10, 1000], ["chr1", 20000, 111000], ["chr2", 22222, 33333]],
        "target_info": [],
        "reo_accesion_id": effect_source.accession_id,
        "effect_size": -0.0660384670056446,
        "p_value": 3.19229500470051e-06,
        "sig": 0.000427767530629869,
        "expr_accession_id": "DCPEXPR00000002",
        "expr_name": experiment.name,
        "analysis_accession_id": analysis_accession_id,
    } in json_content["significant reos"][0][1]


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_invalid_region(login_client: SearchClient):
    response = login_client.get("/exp_data/sigdata?region=ch1:1-100000")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_no_region(login_client: SearchClient):
    response = login_client.get("/exp_data/sigdata?expr=DCPEXPR00000002&datasource=both")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_oversize_region(login_client: SearchClient):
    response = login_client.get("/exp_data/sigdata?region=chr1:1-10000000000")
    assert response.status_code == 400


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_backwards_region(login_client: SearchClient):
    response = login_client.get("/exp_data/sigdata?region=chr1:10000-10")
    assert response.status_code == 400
