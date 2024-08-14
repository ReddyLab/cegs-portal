from io import StringIO
from time import sleep

import pytest
from django.core.exceptions import BadRequest
from django.http import Http404

from cegs_portal.conftest import RequestBuilder
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
from cegs_portal.get_expr_data.views import (
    ExperimentDataProgressView,
    ExperimentDataView,
    LocationExperimentDataView,
    RequestExperimentDataView,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def status_view():
    return ExperimentDataProgressView.as_view()


@pytest.fixture
def file_view():
    return ExperimentDataView.as_view()


@pytest.fixture
def loc_view():
    return LocationExperimentDataView.as_view()


@pytest.fixture
def req_view():
    return RequestExperimentDataView.as_view()


@pytest.mark.parametrize(
    "accession_id,valid",
    [
        ("DCPEXPR0000000002", True),
        ("DCPEXPRAAAAAAAAAA", True),
        ("DCPEXP00000002", False),
        ("DCPEXPR000000000F", True),
        ("DCPEXPR000000000G", False),
    ],
)
def test_validate_expr(accession_id, valid):
    assert validate_expr(accession_id) == valid


@pytest.mark.parametrize(
    "filename,valid",
    [
        ("DCPEXPR0000000002.DCPEXPR0000000003.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv", True),
        ("DCPEXPR0000000002.DCPEXPR0000000003.981152cc-67da-403f-97e1-b2ff5c1051f8", False),
        ("DCPEXPR0000000002.DCPEXPR0000000003.981152cc-67da-403f-97e1-b2ff5c1051f.tsv", False),
        ("DCPEXPR0000000002.DCPEXPR000000000K.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv", False),
        ("DCPEXPR000000000K.DCPEXPR0000000003.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv", False),
    ],
)
def test_validate_filename(filename, valid):
    assert validate_filename(filename) == valid


@pytest.mark.parametrize(
    "expr_accession_ids,an_accession_ids,valid",
    [
        (["DCPEXPR0000000002"], [], True),
        (["DCPEXPR0000000002", "DCPEXPR0000000003"], [], True),
        (["DCPEXPR000000000K"], [], False),
        (["DCPEXPR0000000002", "DCPXPR00000003"], [], False),
        ([], ["DCPAN0000000002"], True),
        ([], ["DCPAN0000000002", "DCPAN0000000003"], True),
        ([], ["DCPAN000000000K"], False),
        ([], ["DCPAN0000000002", "DCPN00000003"], False),
        (["DCPEXPR0000000002"], ["DCPAN0000000002"], True),
        (["DCPEXPR0000000002", "DCPEXPR0000000003"], ["DCPAN0000000002", "DCPAN0000000003"], True),
        (["DCPEXPR000000000K"], ["DCPAN000000000K"], False),
        (["DCPEXPR0000000002", "DCPXPR00000003"], ["DCPAN0000000002", "DCPN00000003"], False),
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
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], Facets(), ReoDataSource.BOTH
    )

    assert len(result) == 2


@pytest.mark.usefixtures("private_reg_effects")
def test_retrieve_private_experiment_data_no_exprs():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], Facets(), ReoDataSource.BOTH
    )

    assert len(result) == 0


@pytest.mark.usefixtures("private_reg_effects")
def test_retrieve_private_experiment_data_with_expr():
    result = retrieve_experiment_data(
        ["DCPEXPR0000000002"],
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)],
        ["DCPEXPR0000000002"],
        [],
        Facets(),
        ReoDataSource.BOTH,
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_source_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], Facets(), ReoDataSource.SOURCES
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_target_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], Facets(), ReoDataSource.TARGETS
    )

    assert len(result) == 1


@pytest.mark.parametrize(
    "cat_facets,effect_size,sig,result_count",
    [
        ([], (-10, 0), (None, None), 2),
        ([], (0, 10), (None, None), 0),
        ([], (None, None), (4.3979400087, 100.0), 0),
        ([], (None, None), (2.3010299957, 100.0), 2),
        ([], (-10, 0), (2.3010299957, 100.0), 2),
        ([], (0, 10), (2.3010299957, 100.0), 0),
        ([], (-10, 0), (4.3979400087, 100.0), 0),
        ([], (0, 10), (4.3979400087, 100.0), 0),
    ],
)
@pytest.mark.usefixtures("reg_effects")
def test_retrieve_num_facet_experiment_data(cat_facets, effect_size, sig, result_count):
    facets = Facets(categorical_facets=cat_facets, effect_size_range=effect_size, sig_range=sig)
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == result_count


def test_retrieve_cat_facet_experiment_data(reg_effects):
    _, _, enriched, depleted, nonsig, _ = reg_effects
    facets = Facets(categorical_facets=[])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 2

    facets = Facets(categorical_facets=[enriched.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 1

    facets = Facets(categorical_facets=[depleted.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 0

    facets = Facets(categorical_facets=[nonsig.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 1

    facets = Facets(categorical_facets=[depleted.id, nonsig.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 1

    facets = Facets(categorical_facets=[enriched.id, depleted.id, nonsig.id])
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], facets, ReoDataSource.BOTH
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_facet_source_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], Facets(), ReoDataSource.SOURCES
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_facet_target_experiment_data():
    result = retrieve_experiment_data(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], Facets(), ReoDataSource.TARGETS
    )

    assert len(result) == 1


def test_list_experiment_data(reg_effects):
    _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    results = output_experiment_data_list(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR0000000002"], [], ReoDataSource.BOTH
    )

    assert results == [
        {
            "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
            "targets": [],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR0000000002",
            "analysis id": analysis_accession_id,
        },
        {
            "source locs": ["chr1:11-1001", "chr2:22223-33334"],
            "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR0000000002",
            "analysis id": analysis_accession_id,
        },
    ]


def test_list_analysis_data(reg_effects):
    _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    results = output_experiment_data_list(
        [], [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], [], [analysis_accession_id], ReoDataSource.BOTH
    )

    assert results == [
        {
            "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
            "targets": [],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR0000000002",
            "analysis id": analysis_accession_id,
        },
        {
            "source locs": ["chr1:11-1001", "chr2:22223-33334"],
            "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
            "p-val": 0.00000319229500470051,
            "adj p-val": 0.000427767530629869,
            "effect size": -0.0660384670056446,
            "expr id": "DCPEXPR0000000002",
            "analysis id": analysis_accession_id,
        },
    ]


def test_location_experiment_data(reg_effects, login_test_client: RequestBuilder, loc_view):
    _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    response = login_test_client.get(
        "/exp_data/location?region=chr1:1-100000&expr=DCPEXPR0000000002&datasource=both"
    ).request(loc_view)
    assert response.status_code == 200

    json_content = response.json()
    assert json_content == {
        "experiment data": [
            {
                "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
                "targets": [],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR0000000002",
                "analysis id": analysis_accession_id,
            },
            {
                "source locs": ["chr1:11-1001", "chr2:22223-33334"],
                "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR0000000002",
                "analysis id": analysis_accession_id,
            },
        ]
    }


def test_location_analysis_data(reg_effects, login_test_client: RequestBuilder, loc_view):
    _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    response = login_test_client.get(
        f"/exp_data/location?region=chr1:1-100000&an={analysis_accession_id}&datasource=both"
    ).request(loc_view)
    assert response.status_code == 200

    json_content = response.json()
    assert json_content == {
        "experiment data": [
            {
                "source locs": ["chr1:10-1000", "chr1:20000-111000", "chr2:22222-33333"],
                "targets": [],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR0000000002",
                "analysis id": analysis_accession_id,
            },
            {
                "source locs": ["chr1:11-1001", "chr2:22223-33334"],
                "targets": [{"gene sym": "XUEQ-1", "gene id": "ENSG01124619313"}],
                "p-val": 0.00000319229500470051,
                "adj p-val": 0.000427767530629869,
                "effect size": -0.0660384670056446,
                "expr id": "DCPEXPR0000000002",
                "analysis id": analysis_accession_id,
            },
        ]
    }


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_invalid_region(login_test_client: RequestBuilder, loc_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/exp_data/location?region=ch1:1-100000&expr=DCPEXPR0000000002&datasource=both").request(
            loc_view
        )


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_no_region(login_test_client: RequestBuilder, loc_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/exp_data/location?expr=DCPEXPR0000000002&datasource=both").request(loc_view)


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_oversize_region(login_test_client: RequestBuilder, loc_view):
    with pytest.raises(BadRequest):
        login_test_client.get(
            "/exp_data/location?region=chr1:1-10000000000&expr=DCPEXPR0000000002&datasource=both"
        ).request(loc_view)


@pytest.mark.usefixtures("reg_effects")
def test_location_experiment_data_backwards_region(login_test_client: RequestBuilder, loc_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/exp_data/location?region=chr1:10000-10&expr=DCPEXPR0000000002&datasource=both").request(
            loc_view
        )


def test_write_experiment_data(reg_effects):
    _, _, _, _, _, experiment = reg_effects
    analysis_accession_id = experiment.analyses.first().accession_id
    experiment_data = list(
        retrieve_experiment_data(
            [],
            [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)],
            ["DCPEXPR0000000002"],
            [],
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
        f"chr1:10-1000,chr1:20000-111000,chr2:22222-33333\t\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR0000000002\t{analysis_accession_id}\n"  # noqa: E501
        f"chr1:11-1001,chr2:22223-33334\tXUEQ-1:ENSG01124619313\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR0000000002\t{analysis_accession_id}\n"  # noqa: E501
    )


def test_write_analysis_data(reg_effects):
    _, _, _, _, _, experiment = reg_effects
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
        f"chr1:10-1000,chr1:20000-111000,chr2:22222-33333\t\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR0000000002\t{analysis_accession_id}\n"  # noqa: E501
        f"chr1:11-1001,chr2:22223-33334\tXUEQ-1:ENSG01124619313\t0.00000319229500470051\t0.000427767530629869\t-0.0660384670056446\tDCPEXPR0000000002\t{analysis_accession_id}\n"  # noqa: E501
    )


@pytest.mark.usefixtures("reg_effects")
def test_request_experiment_data(login_test_client: RequestBuilder, file_view, req_view, status_view):
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = login_test_client.post(
        "/exp_data/request?expr=DCPEXPR0000000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    ).request(req_view)
    assert response.status_code == 200
    sleep(0.1)
    json_content = response.json()
    filename = json_content["file location"].split("/")[-1]
    loc_response = login_test_client.get(json_content["file location"]).request(file_view, filename=filename)
    assert loc_response.status_code == 200

    prog_response = login_test_client.get(json_content["file progress"]).request(status_view, filename=filename)
    assert prog_response.status_code == 200


def test_download_experiment_data_success(login_test_client: RequestBuilder, file_view, req_view):
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = login_test_client.post(
        "/exp_data/request?expr=DCPEXPR0000000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    ).request(req_view)
    assert response.status_code == 200
    sleep(0.1)
    json_content = response.json()
    filename = json_content["file location"].split("/")[-1]
    loc_response = login_test_client.get(json_content["file location"]).request(file_view, filename=filename)
    assert loc_response.status_code == 200
    content = StringIO()
    for data in loc_response.streaming_content:
        content.write(data.decode())
    assert len(content.getvalue()) > 0


def test_experiment_data_status_success(login_test_client: RequestBuilder, req_view, status_view):
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = login_test_client.post(
        "/exp_data/request?expr=DCPEXPR0000000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    ).request(req_view)
    assert response.status_code == 200
    sleep(0.1)
    json_content = response.json()
    filename = json_content["file location"].split("/")[-1]
    status_response = login_test_client.get(json_content["file progress"]).request(status_view, filename=filename)
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["file progress"] == "ready"


def test_experiment_data_status_failure(
    login_test_client: RequestBuilder, public_test_client: RequestBuilder, req_view, status_view
):
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = login_test_client.post(
        "/exp_data/request?expr=DCPEXPR0000000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    ).request(req_view)
    assert response.status_code == 200
    sleep(0.1)
    json_content = response.json()
    filename = json_content["file location"].split("/")[-1]
    status_response = public_test_client.get(json_content["file progress"]).request(status_view, filename=filename)
    assert status_response.status_code == 302


def test_download_experiment_data_fail(login_test_client: RequestBuilder, file_view):
    with pytest.raises(Http404):
        login_test_client.get("/exp_data/file/DCPEXPR0000000002.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv").request(
            file_view, filename="DCPEXPR0000000002.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv"
        )


def test_download_experiment_data_invalid_filename(login_test_client: RequestBuilder, file_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/exp_data/file/DCPEXPR000000000K.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv").request(
            file_view, filename="DCPEXPR000000000K.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv"
        )


@pytest.mark.usefixtures("reg_effects")
def test_sig_reo_loc_search():
    result = sig_reo_loc_search(("chr1", 1, 1000000))

    assert len(result[0][1]) == 1


def test_private_sig_reo_loc_search(private_reg_effects):
    _, _, _, _, _, experiment = private_reg_effects
    result = sig_reo_loc_search(("chr1", 1, 1000000))

    assert len(result) == 0

    result = sig_reo_loc_search(("chr1", 1, 1000000), experiments=[experiment.accession_id])

    assert len(result[0][1]) == 1
