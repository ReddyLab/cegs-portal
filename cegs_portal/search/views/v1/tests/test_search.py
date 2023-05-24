import json
from typing import cast

import pytest
from django.test import Client

from cegs_portal.conftest import SearchClient
from cegs_portal.search.models import ChromosomeLocation, DNAFeature
from cegs_portal.search.models.utils import IdType
from cegs_portal.search.views.v1.search import (
    ParseWarning,
    SearchType,
    parse_query,
    parse_source_locs_html,
    parse_source_locs_json,
    parse_source_target_data_html,
    parse_source_target_data_json,
    parse_target_info_html,
    parse_target_info_json,
)


@pytest.mark.parametrize(
    "query, result",
    [
        ("", (None, [], None, None, set())),
        ("hg38", (None, [], None, "GRCh38", set())),
        ("hg19", (None, [], None, "GRCh37", set())),
        ("BRCA2", (SearchType.ID, [(IdType.GENE_NAME, "BRCA2")], None, None, set())),
        ("brca2", (SearchType.ID, [(IdType.GENE_NAME, "brca2")], None, None, set())),
        ("chr1:1-100", (SearchType.LOCATION, [], ChromosomeLocation("chr1", "1", "100"), None, set())),
        ("ch1:1-100", (None, [], None, None, set())),
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
        ("DCPGENE00000000", (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE00000000")], None, None, set())),
        (
            "DCPGENE00000000 hg19",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "hg19 DCPGENE00000000",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "   hg19    DCPGENE00000000    ",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "   hg19    DCPGENE00000000    ",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE00000000")], None, "GRCh37", set()),
        ),
        (
            "hg19 DCPGENE00000000 DCPGENE00000001",
            (
                SearchType.ID,
                [
                    IdType.ACCESSION.associate("DCPGENE00000000"),
                    IdType.ACCESSION.associate("DCPGENE00000001"),
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
                [IdType.ACCESSION.associate("DCPGENE00000000"), IdType.ENSEMBL.associate("ENSG00000001")],
                None,
                "GRCh37",
                set(),
            ),
        ),
        (
            "DCPGENE00000000,hg19,ENSG00000001",
            (
                SearchType.ID,
                [IdType.ACCESSION.associate("DCPGENE00000000"), IdType.ENSEMBL.associate("ENSG00000001")],
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
                [IdType.ENSEMBL.associate("ENSG00000001"), IdType.ACCESSION.associate("DCPGENE00000000")],
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
            "hg19 chr1:1-100 brca2 DCPGENE00000000 ENSG00000001 chr2:2-200 CBX2",
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


def test_experiment_feature_loc_json(client: Client, search_feature: DNAFeature):
    response = client.get(
        f"/search/results/?query={search_feature.chrom_name}%3A{search_feature.location.lower - 10}-{search_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )

    assert response.status_code == 200
    json_content = json.loads(response.content)

    assert json_content["location"] == {
        "assembly": None,
        "chromosome": search_feature.chrom_name,
        "start": search_feature.location.lower - 10,
        "end": search_feature.location.upper + 10,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_anonymous_client(
    client: Client, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    response = client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_authenticated_client(
    login_client: SearchClient, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    response = login_client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_authenticated_authorized_client(
    login_client: SearchClient, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, private_feature, archived_feature = nearby_feature_mix

    login_client.set_user_experiments(
        [private_feature.experiment_accession_id, archived_feature.experiment_accession_id]
    )
    response = login_client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_experiment_feature_loc_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, private_feature, archived_feature = nearby_feature_mix

    assert private_feature.experiment_accession_id is not None
    assert archived_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments(
        [
            cast(str, private_feature.experiment_accession_id),
            cast(str, archived_feature.experiment_accession_id),
        ]
    )

    response = group_login_client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_experiment_feature_accession_redirect(client: Client, search_feature: DNAFeature):
    response = client.get(f"/search/results/?query={search_feature.accession_id}&accept=application/json")  # noqa: E501

    assert response.status_code == 303


def test_experiment_feature_ensembl_redirect(client: Client, search_feature: DNAFeature):
    response = client.get(f"/search/results/?query={search_feature.ensembl_id}&accept=application/json")  # noqa: E501

    assert response.status_code == 303


def test_experiment_feature_name_redirect(client: Client, search_feature: DNAFeature):
    response = client.get(f"/search/results/?query={search_feature.name}&accept=application/json")  # noqa: E501

    assert response.status_code == 303


def test_experiment_feature_accession_json(client: Client, search_feature: DNAFeature, private_feature: DNAFeature):
    response = client.get(
        f"/search/results/?query={search_feature.accession_id}+{private_feature.accession_id}&accept=application/json"
    )  # noqa: E501

    assert response.status_code == 200
    json_content = json.loads(response.content)

    width = search_feature.location.upper - search_feature.location.lower
    browser_padding = width // 10

    assert json_content["location"] == {
        "assembly": search_feature.ref_genome,
        "chromosome": search_feature.chrom_name,
        "start": max(0, search_feature.location.lower - browser_padding),
        "end": search_feature.location.upper + browser_padding,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_with_anonymous_client(
    client: Client, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_with_authenticated_client(
    login_client: SearchClient, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = login_client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_with_authenticated_authorized_client(
    login_client: SearchClient, search_feature: DNAFeature, private_feature: DNAFeature
):
    login_client.set_user_experiments([private_feature.experiment_accession_id])
    response = login_client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_experiment_feature_accession_with_authenticated_authorized_group_client(
    group_login_client: SearchClient,
    search_feature: DNAFeature,
    private_feature: DNAFeature,
):
    assert private_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])

    response = group_login_client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_archived_experiment_feature_accession_with_anonymous_client(
    client: Client, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_accession_with_authenticated_client(
    login_client: SearchClient, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = login_client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_accession_with_authenticated_authorized_client(
    login_client: SearchClient, archived_feature: DNAFeature, search_feature: DNAFeature
):
    login_client.set_user_experiments([archived_feature.experiment_accession_id])
    response = login_client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_accession_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, archived_feature: DNAFeature, search_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_json(client: Client, feature: DNAFeature, private_feature: DNAFeature):
    response = client.get(
        f"/search/results/?query={feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    )  # noqa: E501

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


def test_experiment_feature_ensembl_with_anonymous_client(
    client: Client, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_with_authenticated_client(
    login_client: SearchClient, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = login_client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_with_authenticated_authorized_client(
    login_client: SearchClient, search_feature: DNAFeature, private_feature: DNAFeature
):
    login_client.set_user_experiments([private_feature.experiment_accession_id])
    response = login_client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_experiment_feature_ensembl_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, search_feature: DNAFeature, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 2


def test_archived_experiment_feature_ensembl_with_anonymous_client(
    client: Client, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_ensembl_with_authenticated_client(
    login_client: SearchClient, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = login_client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_ensembl_with_authenticated_authorized_client(
    login_client: SearchClient, archived_feature: DNAFeature, search_feature: DNAFeature
):
    login_client.set_user_experiments([archived_feature.experiment_accession_id])
    response = login_client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_ensembl_with_authenticated_authorized_group_client(
    group_login_client: SearchClient, archived_feature: DNAFeature, search_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])
    response = group_login_client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    )
    assert response.status_code == 200

    json_content = json.loads(response.content)
    assert len(json_content["features"]) == 1


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


def test_parse_source_locs_html():
    assert parse_source_locs_html('{(chr1,\\"[1,2)\\")}') == "chr1:1-2"
    assert parse_source_locs_html('{(chr1,\\"[1,2)\\"),(chr2,\\"[2,4)\\")}') == "chr1:1-2, chr2:2-4"


def test_parse_source_locs_json():
    assert parse_source_locs_json('{(chr1,\\"[1,2)\\")}') == [("chr1", 1, 2)]
    assert parse_source_locs_json('{(chr1,\\"[1,2)\\"),(chr2,\\"[2,4)\\")}') == [("chr1", 1, 2), ("chr2", 2, 4)]


def test_parse_source_target_data_html():
    test_data = {
        "target_info": '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}',
        "source_locs": '{(chr1,\\"[1,2)\\")}',
        "asdf": 1234,
    }
    assert parse_source_target_data_html(test_data) == {
        "target_info": "ZBTB12",
        "source_locs": "chr1:1-2",
        "asdf": 1234,
    }


def test_parse_source_target_data_json():
    test_data = {
        "target_info": '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}',
        "source_locs": '{(chr1,\\"[1,2)\\")}',
        "asdf": 1234,
    }
    assert parse_source_target_data_json(test_data) == {
        "target_info": [("ZBTB12", "ENSG00000204366")],
        "source_locs": [("chr1", 1, 2)],
        "asdf": 1234,
    }


def test_parse_target_info_html():
    assert parse_target_info_html('{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}') == "ZBTB12"
    assert (
        parse_target_info_html(
            '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)","(chr6,\\"[8386234,2389234)\\",HLA-A,ENSG00000204367)"}'  # noqa: E501
        )
        == "ZBTB12, HLA-A"
    )


def test_parse_target_info_json():
    assert parse_target_info_json('{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}') == [
        ("ZBTB12", "ENSG00000204366")
    ]
    assert parse_target_info_json(
        '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)","(chr6,\\"[8386234,2389234)\\",HLA-A,ENSG00000204367)"}'  # noqa: E501
    ) == [("ZBTB12", "ENSG00000204366"), ("HLA-A", "ENSG00000204367")]
