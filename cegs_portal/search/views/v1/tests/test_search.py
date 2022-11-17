import json
from typing import Tuple

import pytest
from django.test import Client

from cegs_portal.search.models import ChromosomeLocation, DNAFeature
from cegs_portal.search.models.utils import QueryToken
from cegs_portal.search.views.v1.search import ParseWarning, SearchType, parse_query
from cegs_portal.users.models import GroupExtension


@pytest.mark.parametrize(
    "query, result",
    [
        ("", (None, [], None, None, set())),
        ("hg38", (None, [], None, "GRCh38", set())),
        ("hg19", (None, [], None, "GRCh37", set())),
        ("chr1:1-100", (SearchType.LOCATION, [], ChromosomeLocation("chr1", "1", "100"), None, set())),
        (
            "chr1:1-100 chr2: 2-200",
            (SearchType.LOCATION, [], ChromosomeLocation("chr1", "1", "100"), None, {ParseWarning.TOO_MANY_LOCS}),
        ),
        (
            "   chr1:1-100    chr2: 2-200   ",
            (SearchType.LOCATION, [], ChromosomeLocation("chr1", "1", "100"), None, {ParseWarning.TOO_MANY_LOCS}),
        ),
        ("   hg38   ", (None, [], None, "GRCh38", set())),
        ("   hg19 hg38   ", (None, [], None, "GRCh38", set())),
        ("DCPGENE00000000", (SearchType.ID, [QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, None, set())),
        (
            "DCPGENE00000000 hg19",
            (SearchType.ID, [QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "hg19 DCPGENE00000000",
            (SearchType.ID, [QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "   hg19    DCPGENE00000000    ",
            (SearchType.ID, [QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "   hg19    DCPGENE00000000    ",
            (SearchType.ID, [QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "hg19 DCPGENE00000000 DCPGENE00000001",
            (
                SearchType.ID,
                [
                    QueryToken.ACCESSION_ID.associate("DCPGENE00000000"),
                    QueryToken.ACCESSION_ID.associate("DCPGENE00000001"),
                ],
                None,
                "GRCh37",
                set(),
            ),
        ),
        (
            "hg19, DCPGENE00000000, ENSG00000001",
            (
                SearchType.ID,
                [QueryToken.ACCESSION_ID.associate("DCPGENE00000000"), QueryToken.ENSEMBL_ID.associate("ENSG00000001")],
                None,
                "GRCh37",
                set(),
            ),
        ),
        (
            "DCPGENE00000000,hg19,ENSG00000001",
            (
                SearchType.ID,
                [QueryToken.ACCESSION_ID.associate("DCPGENE00000000"), QueryToken.ENSEMBL_ID.associate("ENSG00000001")],
                None,
                "GRCh37",
                set(),
            ),
        ),
        (
            "hg19 chr1:1-100 DCPGENE00000000 ENSG00000001",
            (
                SearchType.LOCATION,
                [],
                ChromosomeLocation("chr1", "1", "100"),
                "GRCh37",
                {ParseWarning.IGNORE_TERMS},
            ),
        ),
        (
            " hg19 ENSG00000001   chr1:1-100 DCPGENE00000000 ",
            (
                SearchType.ID,
                [QueryToken.ENSEMBL_ID.associate("ENSG00000001"), QueryToken.ACCESSION_ID.associate("DCPGENE00000000")],
                None,
                "GRCh37",
                {ParseWarning.IGNORE_LOC},
            ),
        ),
        (
            "hg19 chr1:1-100 BRCA2 DCPGENE00000000 ENSG00000001 CBX2",
            (
                SearchType.LOCATION,
                [],
                ChromosomeLocation("chr1", "1", "100"),
                "GRCh37",
                {ParseWarning.IGNORE_TERMS},
            ),
        ),
        (
            "hg19 chr1:1-100 BRCA2 DCPGENE00000000 ENSG00000001 chr2:2-200 CBX2",
            (
                SearchType.LOCATION,
                [],
                ChromosomeLocation("chr1", "1", "100"),
                "GRCh37",
                {ParseWarning.TOO_MANY_LOCS, ParseWarning.IGNORE_TERMS},
            ),
        ),
    ],
)
def test_parse_query(query, result):
    assert parse_query(query) == result


pytestmark = pytest.mark.django_db


def test_experiment_json(client: Client):
    response = client.get("/search/results/?query=chr1%3A0-1000000+hg19&accept=application/json")

    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert json_content["location"] == {
        "assembly": "GRCh37",
        "chromosome": "chr1",
        "start": 0,
        "end": 1_000_000,
    }
    assert len(json_content["features"]) == 0


def test_experiment_feature_loc_json(client: Client, feature: DNAFeature):
    response = client.get(
        f"/search/results/?query={feature.chrom_name}%3A{feature.location.lower - 10}-{feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["location"] == {
        "assembly": None,
        "chromosome": feature.chrom_name,
        "start": feature.location.lower - 10,
        "end": feature.location.upper + 10,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_anonymous_client(client: Client, nearby_feature_mix: Tuple[DNAFeature]):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    response = client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_authenticated_client(
    client: Client, nearby_feature_mix: Tuple[DNAFeature], django_user_model
):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_authenticated_authorized_client(
    client: Client, nearby_feature_mix: Tuple[DNAFeature], django_user_model
):
    pub_feature, private_feature, archived_feature = nearby_feature_mix

    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [private_feature.experiment_accession_id, archived_feature.experiment_accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_experiment_feature_loc_with_authenticated_authorized_group_client(
    client: Client, nearby_feature_mix: Tuple[DNAFeature], group_extension: GroupExtension, django_user_model
):
    pub_feature, private_feature, archived_feature = nearby_feature_mix

    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    group_extension.experiments = [private_feature.experiment_accession_id, archived_feature.experiment_accession_id]
    group_extension.save()
    user.groups.add(group_extension.group)
    user.save()
    client.login(username=username, password=password)
    response = client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_experiment_feature_accession_json(client: Client, feature: DNAFeature):
    response = client.get(f"/search/results/?query={feature.accession_id}&accept=application/json")  # noqa: E501

    assert response.status_code == 200
    json_content = json.loads(response.content)

    width = feature.location.upper - feature.location.lower
    browser_padding = width // 10

    assert json_content["location"] == {
        "assembly": feature.ref_genome,
        "chromosome": feature.chrom_name,
        "start": max(0, feature.location.lower - browser_padding),
        "end": feature.location.upper + browser_padding,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_with_anonymous_client(client: Client, private_feature: DNAFeature):
    response = client.get(f"/search/results/?query={private_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_experiment_feature_accession_with_authenticated_client(
    client: Client, private_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={private_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_experiment_feature_accession_with_authenticated_authorized_client(
    client: Client, private_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [private_feature.experiment_accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={private_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_with_authenticated_authorized_group_client(
    client: Client, private_feature: DNAFeature, group_extension: GroupExtension, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    group_extension.experiments = [private_feature.experiment_accession_id]
    group_extension.save()
    user.groups.add(group_extension.group)
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={private_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_accession_with_anonymous_client(client: Client, archived_feature: DNAFeature):
    response = client.get(f"/search/results/?query={archived_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_archived_experiment_feature_accession_with_authenticated_client(
    client: Client, archived_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={archived_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_archived_experiment_feature_accession_with_authenticated_authorized_client(
    client: Client, archived_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [archived_feature.experiment_accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={archived_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_archived_experiment_feature_accession_with_authenticated_authorized_group_client(
    client: Client, archived_feature: DNAFeature, group_extension: GroupExtension, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    group_extension.experiments = [archived_feature.experiment_accession_id]
    group_extension.save()
    user.groups.add(group_extension.group)
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={archived_feature.accession_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_experiment_feature_ensembl_json(client: Client, feature: DNAFeature):
    response = client.get(f"/search/results/?query={feature.ensembl_id}&accept=application/json")  # noqa: E501

    assert response.status_code == 200
    json_content = json.loads(response.content)

    width = feature.location.upper - feature.location.lower
    browser_padding = width // 10

    assert json_content["location"] == {
        "assembly": feature.ref_genome,
        "chromosome": feature.chrom_name,
        "start": max(0, feature.location.lower - browser_padding),
        "end": feature.location.upper + browser_padding,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_with_anonymous_client(client: Client, private_feature: DNAFeature):
    response = client.get(f"/search/results/?query={private_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_experiment_feature_ensembl_with_authenticated_client(
    client: Client, private_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={private_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_experiment_feature_ensembl_with_authenticated_authorized_client(
    client: Client, private_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [private_feature.experiment_accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={private_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_with_authenticated_authorized_group_client(
    client: Client, private_feature: DNAFeature, group_extension: GroupExtension, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    group_extension.experiments = [private_feature.experiment_accession_id]
    group_extension.save()
    user.groups.add(group_extension.group)
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={private_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_ensembl_with_anonymous_client(client: Client, archived_feature: DNAFeature):
    response = client.get(f"/search/results/?query={archived_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_archived_experiment_feature_ensembl_with_authenticated_client(
    client: Client, archived_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={archived_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_archived_experiment_feature_ensembl_with_authenticated_authorized_client(
    client: Client, archived_feature: DNAFeature, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    user.experiments = [archived_feature.experiment_accession_id]
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={archived_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_archived_experiment_feature_ensembl_with_authenticated_authorized_group_client(
    client: Client, archived_feature: DNAFeature, group_extension: GroupExtension, django_user_model
):
    username = "user1"
    password = "bar"
    user = django_user_model.objects.create_user(username=username, password=password)
    group_extension.experiments = [archived_feature.experiment_accession_id]
    group_extension.save()
    user.groups.add(group_extension.group)
    user.save()
    client.login(username=username, password=password)
    response = client.get(f"/search/results/?query={archived_feature.ensembl_id}&accept=application/json")
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 0


def test_experiment_html(client: Client):
    response = client.get("/search/results/?query=chr1%3A0-1000000")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_experiment_no_query_json(client: Client):
    response = client.get("/search/results/?accept=application/json")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 400


def test_experiment_no_query_html(client: Client):
    response = client.get("/search/results/")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 400
