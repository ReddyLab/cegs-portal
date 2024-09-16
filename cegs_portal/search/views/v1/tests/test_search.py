import re
from typing import cast

import pytest
from django.core.exceptions import BadRequest
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.models import ChromosomeLocation, DNAFeature
from cegs_portal.search.models.utils import IdType
from cegs_portal.search.views.v1.search import (
    FeatureSignificantREOsView,
    ParseWarning,
    SearchType,
    SearchView,
    SignificantExperimentDataView,
    parse_query,
    parse_source_locs_html,
    parse_source_target_data_html,
    parse_target_info_html,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def search_view():
    return SearchView.as_view()


@pytest.fixture
def sig_data_view():
    return SignificantExperimentDataView.as_view()


@pytest.fixture
def sig_reo_view():
    return FeatureSignificantREOsView.as_view()


@pytest.mark.parametrize(
    "query, result",
    [
        ("", (None, [], None, "hg38", set())),
        ("hg38", (None, [], None, "hg38", set())),
        ("hg19", (None, [], None, "hg19", set())),
        ("BRCA2", (SearchType.ID, [(IdType.GENE_NAME, "BRCA2")], None, "hg38", set())),
        ("brca2", (SearchType.ID, [(IdType.GENE_NAME, "brca2")], None, "hg38", set())),
        ("chr1:1-100", (SearchType.LOCATION, [], ChromosomeLocation("chr1", "1", "100"), "hg38", set())),
        ("ch1:1-100", (None, [], None, "hg38", set())),
        (
            "chr1:1-100 chr2: 2-200",
            (SearchType.LOCATION, [], ChromosomeLocation("chr1", "1", "100"), "hg38", {ParseWarning.TOO_MANY_LOCS}),
        ),
        (
            "   chr1:1-100    chr2: 2-200   ",
            (SearchType.LOCATION, [], ChromosomeLocation("chr1", "1", "100"), "hg38", {ParseWarning.TOO_MANY_LOCS}),
        ),
        ("   hg38   ", (None, [], None, "hg38", set())),
        ("   hg19 hg38   ", (None, [], None, "hg38", set())),
        (
            "DCPGENE0000000000",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE0000000000")], None, "hg38", set()),
        ),
        (
            "DCPGENE0000000000 hg19",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE0000000000")], None, "hg19", set()),
        ),
        (
            "hg19 DCPGENE0000000000",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE0000000000")], None, "hg19", set()),
        ),
        (
            "   hg19    DCPGENE0000000000    ",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE0000000000")], None, "hg19", set()),
        ),
        (
            "   hg19    DCPGENE0000000000    ",
            (SearchType.ID, [IdType.ACCESSION.associate("DCPGENE0000000000")], None, "hg19", set()),
        ),
        (
            "hg19 DCPGENE0000000000 DCPGENE0000000001",
            (
                SearchType.ID,
                [
                    IdType.ACCESSION.associate("DCPGENE0000000000"),
                    IdType.ACCESSION.associate("DCPGENE0000000001"),
                ],
                None,
                "hg19",
                set(),
            ),
        ),
        (
            "DCPGENE0000000000 hg19 ENSG00000001",
            (
                SearchType.ID,
                [IdType.ACCESSION.associate("DCPGENE0000000000"), IdType.ENSEMBL.associate("ENSG00000001")],
                None,
                "hg19",
                set(),
            ),
        ),
        (
            "hg19 chr1:1-100 DCPGENE0000000000 ENSG00000001",
            (
                SearchType.LOCATION,
                [],
                ChromosomeLocation("chr1", "1", "100"),
                "hg19",
                {ParseWarning.IGNORE_TERMS},
            ),
        ),
        (
            " hg19 ENSG00000001   chr1:1-100 DCPGENE0000000000 ",
            (
                SearchType.ID,
                [IdType.ENSEMBL.associate("ENSG00000001"), IdType.ACCESSION.associate("DCPGENE0000000000")],
                None,
                "hg19",
                {ParseWarning.IGNORE_LOC},
            ),
        ),
        (
            "hg19 chr1:1-100 BRCA2 DCPGENE0000000000 ENSG00000001 CBX2",
            (
                SearchType.LOCATION,
                [],
                ChromosomeLocation("chr1", "1", "100"),
                "hg19",
                {ParseWarning.IGNORE_TERMS},
            ),
        ),
        (
            "hg19 chr1:1-100 brca2 DCPGENE0000000000 ENSG00000001 chr2:2-200 CBX2",
            (
                SearchType.LOCATION,
                [],
                ChromosomeLocation("chr1", "1", "100"),
                "hg19",
                {ParseWarning.TOO_MANY_LOCS, ParseWarning.IGNORE_TERMS},
            ),
        ),
    ],
)
def test_parse_query(query, result):
    assert parse_query(query) == result


def test_experiment_e2e(client: Client):
    response = client.get("/search/results/?query=chr1%3A0-1000000+hg19&accept=application/json")

    assert response.status_code == 200

    json_content = response.json()
    assert json_content["location"] == {
        "assembly": "hg19",
        "chromosome": "chr1",
        "start": 0,
        "end": 1_000_000,
    }
    assert len(json_content["features"]) == 0


def test_experiment_feature_loc_json(public_test_client: RequestBuilder, search_view, search_feature: DNAFeature):
    response = public_test_client.get(
        f"/search/results/?query={search_feature.chrom_name}%3A{search_feature.location.lower - 10}-{search_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    ).request(search_view)

    assert response.status_code == 200
    json_content = response.json()

    assert json_content["location"] == {
        "assembly": "hg38",
        "chromosome": search_feature.chrom_name,
        "start": search_feature.location.lower - 10,
        "end": search_feature.location.upper + 10,
    }
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_anonymous_client(
    public_test_client: RequestBuilder, search_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    response = public_test_client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


@pytest.mark.usefixtures("reg_effects")
def test_sig_reg_loc_with_anonymous_client(public_test_client: RequestBuilder, search_view):
    response = public_test_client.get("/search/results/?query=chr1%3A1-1000000&accept=application/json").request(
        search_view
    )
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["sig_reg_effects"]) == 1


@pytest.mark.usefixtures("private_reg_effects")
def test_private_sig_reg_loc_with_anonymous_client(public_test_client: RequestBuilder, search_view):
    response = public_test_client.get("/search/results/?query=chr1%3A1-1000000&accept=application/json").request(
        search_view
    )
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["sig_reg_effects"]) == 0


def test_experiment_feature_loc_with_authenticated_client(
    login_test_client: RequestBuilder, search_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    response = login_test_client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_experiment_feature_loc_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, search_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, private_feature, archived_feature = nearby_feature_mix

    login_test_client.set_user_experiments(
        [private_feature.experiment_accession_id, archived_feature.experiment_accession_id]
    )
    response = login_test_client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 2


def test_experiment_feature_loc_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, search_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, private_feature, archived_feature = nearby_feature_mix

    assert private_feature.experiment_accession_id is not None
    assert archived_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments(
        [
            private_feature.experiment_accession_id,
            archived_feature.experiment_accession_id,
        ]
    )

    response = group_login_test_client.get(
        f"/search/results/?query={pub_feature.chrom_name}%3A{pub_feature.location.lower - 10}-{archived_feature.location.upper + 10}&accept=application/json"  # noqa: E501
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 2


def test_experiment_feature_accession_redirect(
    public_test_client: RequestBuilder, search_view, search_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={search_feature.accession_id}&accept=application/json"
    ).request(search_view)

    assert response.status_code == 303


def test_experiment_feature_ensembl_redirect(
    public_test_client: RequestBuilder, search_view, search_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={search_feature.ensembl_id}&accept=application/json"
    ).request(search_view)

    assert response.status_code == 303


def test_experiment_feature_name_redirect(public_test_client: RequestBuilder, search_view, search_feature: DNAFeature):
    response = public_test_client.get(f"/search/results/?query={search_feature.name}&accept=application/json").request(
        search_view
    )

    assert response.status_code == 303


def test_experiment_feature_accession_json(
    public_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={search_feature.accession_id}+{private_feature.accession_id}&accept=application/json"
    ).request(search_view)

    assert response.status_code == 200
    json_content = response.json()

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
    public_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_with_authenticated_client(
    login_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = login_test_client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_experiment_feature_accession_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    login_test_client.set_user_experiments([private_feature.experiment_accession_id])
    response = login_test_client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 2


def test_experiment_feature_accession_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder,
    search_view,
    search_feature: DNAFeature,
    private_feature: DNAFeature,
):
    assert private_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([private_feature.experiment_accession_id])

    response = group_login_test_client.get(
        f"/search/results/?query={private_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 2


def test_archived_experiment_feature_accession_with_anonymous_client(
    public_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_accession_with_authenticated_client(
    login_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = login_test_client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_accession_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    login_test_client.set_user_experiments([archived_feature.experiment_accession_id])
    response = login_test_client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_accession_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])
    response = group_login_test_client.get(
        f"/search/results/?query={archived_feature.accession_id}+{search_feature.accession_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_json(
    public_test_client: RequestBuilder, search_view, feature: DNAFeature, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    ).request(search_view)

    assert response.status_code == 200
    json_content = response.json()

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
    public_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_with_authenticated_client(
    login_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    response = login_test_client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_experiment_feature_ensembl_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    login_test_client.set_user_experiments([private_feature.experiment_accession_id])
    response = login_test_client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 2


def test_experiment_feature_ensembl_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, search_view, search_feature: DNAFeature, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([cast(str, private_feature.experiment_accession_id)])
    response = group_login_test_client.get(
        f"/search/results/?query={search_feature.ensembl_id}+{private_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 2


def test_archived_experiment_feature_ensembl_with_anonymous_client(
    public_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_ensembl_with_authenticated_client(
    login_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    response = login_test_client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_ensembl_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    login_test_client.set_user_experiments([archived_feature.experiment_accession_id])
    response = login_test_client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_archived_experiment_feature_ensembl_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, search_view, archived_feature: DNAFeature, search_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])
    response = group_login_test_client.get(
        f"/search/results/?query={archived_feature.ensembl_id}+{search_feature.ensembl_id}&accept=application/json"
    ).request(search_view)
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content["features"]) == 1


def test_experiment_html(public_test_client: RequestBuilder, search_view):
    response = public_test_client.get("/search/results/?query=chr1%3A0-1000000").request(search_view)

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_experiment_no_query_json(public_test_client: RequestBuilder, search_view):
    with pytest.raises(BadRequest):
        public_test_client.get("/search/results/?accept=application/json").request(search_view)


def test_experiment_no_query_html(public_test_client: RequestBuilder, search_view):
    with pytest.raises(BadRequest):
        public_test_client.get("/search/results/").request(search_view)


def test_parse_source_locs_html():
    assert parse_source_locs_html('{(chr1,\\"[1,2)\\",DCPDHS0000000001)}') == [("chr1:1-2", "DCPDHS0000000001")]
    assert parse_source_locs_html('{(chr1,\\"[1,2)\\",DCPDHS0000000001),(chr2,\\"[2,4)\\",DCPDHS0000000002)}') == [
        ("chr1:1-2", "DCPDHS0000000001"),
        ("chr2:2-4", "DCPDHS0000000002"),
    ]


def test_parse_source_target_data_html():
    test_data = {
        "target_info": '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}',
        "source_locs": '{(chr1,\\"[1,2)\\",DCPDHS0000000001)}',
        "asdf": 1234,
    }
    assert parse_source_target_data_html(test_data) == {
        "target_info": [("ZBTB12", "ENSG00000204366")],
        "source_locs": [("chr1:1-2", "DCPDHS0000000001")],
        "asdf": 1234,
    }


def test_parse_target_info_html():
    assert parse_target_info_html('{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)"}') == [
        ("ZBTB12", "ENSG00000204366")
    ]
    assert parse_target_info_html(
        '{"(chr6,\\"[31867384,31869770)\\",ZBTB12,ENSG00000204366)","(chr6,\\"[8386234,2389234)\\",HLA-A,ENSG00000204367)"}'  # noqa: E501
    ) == [("ZBTB12", "ENSG00000204366"), ("HLA-A", "ENSG00000204367")]


def test_sigdata(reg_effects, client: Client):
    effect_source, _, _, _, _, experiment = reg_effects

    response = client.get("/search/sigdata?region=chr1:1-100000")
    assert response.status_code == 200

    sources = sorted(effect_source.sources.all(), key=lambda x: x.accession_id)

    stripped_response = re.sub(r"\s+", "", response.content.decode("utf-8"), flags=re.MULTILINE)
    # strip out spaces in blank lines

    expected_string = re.sub(
        r"\s+",
        "",
        f"""
    <div class="text-xl font-bold">Most Significant Reg Effect Observations</div>

    <div class="overflow-x-auto">
    <table class="data-table no-hover">
        <tr><th>Enhancer/Gene</th><th>Effect Size</th><th>Corrected p-value</th><th>Raw p-value</th><th>Experiment</th></tr>

            <tr class="">
                <td>
                    <div>Tested Element Locations: <a href="/search/feature/accession/{sources[0].accession_id}">{f"{sources[0].chrom_name}:{sources[0].location.lower:,}-{sources[0].location.upper:,}"}</a>, <a href="/search/feature/accession/{sources[1].accession_id}">{f"{sources[1].chrom_name}:{sources[1].location.lower:,}-{sources[1].location.upper:,}"}</a>, <a href="/search/feature/accession/{sources[2].accession_id}">{f"{sources[2].chrom_name}:{sources[2].location.lower:,}-{sources[2].location.upper:,}"}</a></div>
                </td>
                <td><a href="/search/regeffect/{effect_source.accession_id}">{effect_source.effect_size:.3f}</a></td>
                <td><a href="/search/regeffect/{effect_source.accession_id}">{effect_source.significance:.6f}</a></td>
                <td><a href="/search/regeffect/{effect_source.accession_id}">{effect_source.raw_p_value:.6f}</a></td>
                <td rowspan="1"><a href="/search/experiment/{experiment.accession_id}">{experiment.name}</a></td>
            </tr>
    </table>
    </div>
    """,
    )

    assert stripped_response == expected_string


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_invalid_region(login_test_client: RequestBuilder, sig_data_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/search/sigdata?region=ch1:1-100000").request(sig_data_view)


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_no_region(login_test_client: RequestBuilder, sig_data_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/search/sigdata?expr=DCPEXPR0000000002&datasource=both").request(sig_data_view)


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_oversize_region(login_test_client: RequestBuilder, sig_data_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/search/sigdata?region=chr1:1-10000000000").request(sig_data_view)


@pytest.mark.usefixtures("reg_effects")
def test_sigdata_backwards_region(login_test_client: RequestBuilder, sig_data_view):
    with pytest.raises(BadRequest):
        login_test_client.get("/search/sigdata?region=chr1:10000-10").request(sig_data_view)


def test_feature_sigreo(reg_effects, login_test_client: RequestBuilder, sig_reo_view):
    effect_source, effect_both, _, _, _, experiment = reg_effects

    response = login_test_client.get("/search/feature_sigreo?region=chr1:1-100000").request(sig_reo_view)
    assert response.status_code == 200

    sig_sources = sorted(effect_source.sources.all(), key=lambda x: x.accession_id)

    nonsig_sources = sorted(effect_both.sources.all(), key=lambda x: x.accession_id)
    nonsig_targets = list(effect_both.targets.all())

    response_html = response.content.decode("utf-8")

    for source in sig_sources:
        assert (
            re.search(
                f"{source.chrom_name}: {source.location.lower:,} - {source.location.upper:,}",
                response_html,
                flags=re.MULTILINE,
            )
            is not None
        )

    for source in nonsig_sources:
        assert (
            re.search(
                f"{source.chrom_name}: {source.location.lower:,} - {source.location.upper:,}",
                response_html,
                flags=re.MULTILINE,
            )
            is None
        )
    for target in nonsig_targets:
        assert re.search(target.name, response_html, flags=re.MULTILINE) is None


def test_feature_sigreo_tsv(reg_effects, login_test_client: RequestBuilder, sig_reo_view):
    effect_source, _, _, _, _, _ = reg_effects

    response = login_test_client.get(
        "/search/feature_sigreo?region=chr1:1-100000&accept=text/tab-separated-values"
    ).request(sig_reo_view)
    assert response.status_code == 200

    sig_sources = sorted(effect_source.sources.all(), key=lambda x: x.accession_id)

    response_tsv = response.content.decode("utf-8")

    for source in sig_sources:
        match source.strand:
            case "+":
                strand = r"\+"
            case None:
                strand = "."
            case "-":
                strand = "-"
        gene_dist = source.closest_gene_distance if source.closest_gene_distance is not None else ""
        line = f'{source.chrom_name}\t{source.location.lower}\t{source.location.upper}\t{source.chrom_name}:{source.location.lower}-{source.location.upper}:{strand}:\t0\t{strand}\t{effect_source.effect_size}\t{effect_source.direction}\t{effect_source.significance}\t{gene_dist}\t{source.get_feature_type_display()}\t"{effect_source.experiment.name}"\t{effect_source.accession_id}'
        assert re.search(line, response_tsv) is not None


def test_feature_sigreo_bed6(reg_effects, login_test_client: RequestBuilder, sig_reo_view):
    effect_source, _, _, _, _, _ = reg_effects

    response = login_test_client.get(
        "/search/feature_sigreo?region=chr1:1-100000&accept=text/tab-separated-values&tsv_format=bed6"
    ).request(sig_reo_view)
    assert response.status_code == 200

    sig_sources = sorted(effect_source.sources.all(), key=lambda x: x.accession_id)

    response_tsv = response.content.decode("utf-8")

    for source in sig_sources:
        match source.strand:
            case "+":
                strand = r"\+"
            case None:
                strand = "."
            case "-":
                strand = "-"
        line = f"{source.chrom_name}\t{source.location.lower}\t{source.location.upper}\t{source.chrom_name}:{source.location.lower}-{source.location.upper}:{strand}:\t0\t{strand}"
        assert re.search(line, response_tsv) is not None
