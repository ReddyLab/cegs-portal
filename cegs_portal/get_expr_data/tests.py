import json
from io import StringIO
from time import sleep

import pytest
from django.test import Client

from cegs_portal.get_expr_data.view_models import (
    ReoDataSource,
    gen_output_filename,
    output_experiment_data,
    parse_source_locs,
    parse_target_info,
    retrieve_experiment_data,
    validate_expr,
    validate_filename,
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
    "accession_ids,valid",
    [
        (["DCPEXPR00000002"], True),
        (["DCPEXPR00000002", "DCPEXPR00000003"], True),
        (["DCPEXPR0000000K"], False),
        (["DCPEXPR00000002", "DCPXPR00000003"], False),
    ],
)
def test_gen_output_filename(accession_ids, valid):
    assert validate_filename(gen_output_filename(accession_ids)) == valid


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
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], ReoDataSource.BOTH
    )

    assert len(result) == 3


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_source_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], ReoDataSource.SOURCES
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_retrieve_target_experiment_data():
    result = retrieve_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], ReoDataSource.TARGETS
    )

    assert len(result) == 2


@pytest.mark.usefixtures("reg_effects")
def test_output_experiment_data():
    output_experiment_data(
        [("chr1", 1, 1_000_000), ("chr2", 1, 1_000_000)], ["DCPEXPR00000002"], ReoDataSource.BOTH, "test.tsv"
    )
    assert True


@pytest.mark.usefixtures("reg_effects")
def test_request_experiment_data(client: Client, django_user_model):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.save()
    client.login(username=username, password=password)
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = client.post(
        "/exp_data/request?expr=DCPEXPR00000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    )
    assert response.status_code == 200
    sleep(0.1)
    json_content = json.loads(response.content)
    loc_response = client.get(json_content["file location"])
    assert loc_response.status_code == 200

    prog_response = client.get(json_content["file progress"])
    assert prog_response.status_code == 200


def test_download_experiment_data_success(client: Client, django_user_model):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.save()
    client.login(username=username, password=password)
    bed_file = StringIO("chr1\t1\t1000000\nchr2\t1\t1000000")
    bed_file.name = "test.bed"
    response = client.post(
        "/exp_data/request?expr=DCPEXPR00000002&datasource=both",
        data={"regions": bed_file},
        format="multipart/form-data",
    )
    assert response.status_code == 200
    sleep(0.1)
    json_content = json.loads(response.content)
    loc_response = client.get(json_content["file location"])
    assert loc_response.status_code == 200
    content = StringIO()
    for data in loc_response.streaming_content:
        content.write(data.decode())
    assert len(content.getvalue()) > 0


def test_download_experiment_data_fail(client: Client, django_user_model):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.save()
    client.login(username=username, password=password)
    response = client.get("/exp_data/file/DCPEXPR00000002.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv")
    assert response.status_code == 404


def test_download_experiment_data_invalid_filename(client: Client, django_user_model):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.save()
    client.login(username=username, password=password)
    response = client.get("/exp_data/file/DCPEXPR0000000K.981152cc-67da-403f-97e1-b2ff5c1051f8.tsv")
    assert response.status_code == 400
