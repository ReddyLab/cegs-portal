import re
from typing import cast
from urllib.parse import quote_plus

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import Client

from cegs_portal.conftest import RequestBuilder
from cegs_portal.search.models import DNAFeature, DNAFeatureType
from cegs_portal.search.views.v1 import DNAFeatureId, DNAFeatureLoc

pytestmark = pytest.mark.django_db


@pytest.fixture
def id_view():
    return DNAFeatureId.as_view()


@pytest.fixture
def loc_view():
    return DNAFeatureLoc.as_view()


def check_json_response(response, feature):
    assert response.status_code == 200
    json_content = response.json()
    assert isinstance(json_content, list)
    assert len(json_content) == 1

    response_feature = json_content[0]
    assert response_feature["accession_id"] == feature.accession_id
    assert response_feature["ensembl_id"] == feature.ensembl_id
    assert response_feature["chr"] == feature.chrom_name
    assert response_feature["start"] == feature.location.lower
    assert response_feature["end"] == feature.location.upper - 1
    assert response_feature["strand"] == feature.strand
    assert response_feature["name"] == feature.name
    assert response_feature["ref_genome"] == feature.ref_genome
    assert response_feature["type"] == feature.get_feature_type_display()


def check_tsv_response(response, feature):
    assert response.status_code == 200
    response_tsv = response.content.decode("utf-8")

    match feature.strand:
        case "+":
            strand = r"\+"
        case None:
            strand = "."
        case "-":
            strand = "-"
    gene_dist = feature.closest_gene_distance if feature.closest_gene_distance is not None else ""
    name = feature.name if feature.name is not None else ""
    line = f"{feature.chrom_name}\t{feature.location.lower}\t{feature.location.upper}\t{feature.chrom_name}:{feature.location.lower}-{feature.location.upper}:{strand}:{name}\t0\t{strand}\t{gene_dist}\t{feature.get_feature_type_display()}\t{feature.accession_id}\t{feature.experiment_accession_id}"
    assert re.search(line, response_tsv) is not None


def check_bed_response(response, feature):
    assert response.status_code == 200
    response_tsv = response.content.decode("utf-8")

    match feature.strand:
        case "+":
            strand = r"\+"
        case None:
            strand = "."
        case "-":
            strand = "-"
    name = feature.name if feature.name is not None else ""
    line = f"{feature.chrom_name}\t{feature.location.lower}\t{feature.location.upper}\t{feature.chrom_name}:{feature.location.lower}-{feature.location.upper}:{strand}:{name}\t0\t{strand}"
    assert re.search(line, response_tsv) is not None


def test_get_feature_ensembl_e2e(client: Client, feature: DNAFeature):
    response = client.get(f"/search/feature/ensembl/{feature.ensembl_id}?accept=application/json")
    check_json_response(response, feature)

    response = client.get(f"/search/feature/ensembl/{feature.ensembl_id}")

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_get_no_feature_ensembl_html(public_test_client: RequestBuilder, id_view):
    with pytest.raises(Http404):
        public_test_client.get("/search/feature/ensembl/ENSG0000000000").request(
            id_view, id_type="ensembl", feature_id="ENSG0000000000"
        )


def test_get_feature_ensembl_with_anonymous_client(
    public_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/feature/ensembl/{private_feature.ensembl_id}?accept=application/json"
    ).request(id_view, id_type="ensembl", feature_id=private_feature.ensembl_id)
    assert response.status_code == 302


def test_get_feature_ensembl_with_authenticated_client(
    login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/feature/ensembl/{private_feature.ensembl_id}?accept=application/json").request(
            id_view, id_type="ensembl", feature_id=private_feature.ensembl_id
        )


def test_get_feature_ensembl_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    login_test_client.set_user_experiments([private_feature.experiment_accession_id])
    response = login_test_client.get(
        f"/search/feature/ensembl/{private_feature.ensembl_id}?accept=application/json"
    ).request(id_view, id_type="ensembl", feature_id=private_feature.ensembl_id)
    assert response.status_code == 200


def test_get_feature_ensembl_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([private_feature.experiment_accession_id])
    response = group_login_test_client.get(
        f"/search/feature/ensembl/{private_feature.ensembl_id}?accept=application/json"
    ).request(id_view, id_type="ensembl", feature_id=private_feature.ensembl_id)
    assert response.status_code == 200


def test_get_archived_feature_ensembl_with_anonymous_client(
    public_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        public_test_client.get(
            f"/search/feature/ensembl/{archived_feature.ensembl_id}?accept=application/json"
        ).request(id_view, id_type="ensembl", feature_id=archived_feature.ensembl_id)


def test_get_archived_feature_ensembl_with_authenticated_client(
    login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/feature/ensembl/{archived_feature.ensembl_id}?accept=application/json").request(
            id_view, id_type="ensembl", feature_id=archived_feature.ensembl_id
        )


def test_get_archived_feature_ensembl_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    login_test_client.set_user_experiments([archived_feature.experiment_accession_id])
    with pytest.raises(PermissionDenied):
        login_test_client.get(f"/search/feature/ensembl/{archived_feature.ensembl_id}?accept=application/json").request(
            id_view, id_type="ensembl", feature_id=archived_feature.ensembl_id
        )


def test_get_archived_feature_ensembl_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([archived_feature.experiment_accession_id])
    with pytest.raises(PermissionDenied):
        group_login_test_client.get(
            f"/search/feature/ensembl/{archived_feature.ensembl_id}?accept=application/json"
        ).request(id_view, id_type="ensembl", feature_id=archived_feature.ensembl_id)


def test_get_feature_accession_json(public_test_client: RequestBuilder, id_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/feature/accession/{feature.accession_id}?accept=application/json"
    ).request(id_view, id_type="accession", feature_id=feature.accession_id)
    check_json_response(response, feature)


def test_get_feature_accession_html(public_test_client: RequestBuilder, id_view, feature: DNAFeature):
    response = public_test_client.get(f"/search/feature/accession/{feature.accession_id}").request(
        id_view, id_type="accession", feature_id=feature.accession_id
    )

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_get_no_feature_accession_html(public_test_client: RequestBuilder, id_view):
    with pytest.raises(Http404):
        public_test_client.get("/search/feature/accession/DCPGENE0000000000").request(
            id_view, id_type="accession", feature_id="DCPGENE0000000000"
        )


def test_get_feature_accession_with_anonymous_client(
    public_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/feature/accession/{private_feature.accession_id}?accept=application/json"
    ).request(id_view, id_type="accession", feature_id=private_feature.accession_id)
    assert response.status_code == 302


def test_get_feature_accession_with_authenticated_client(
    login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{private_feature.accession_id}?accept=application/json"
        ).request(id_view, id_type="accession", feature_id=private_feature.accession_id)


def test_get_feature_accession_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    login_test_client.set_user_experiments([private_feature.experiment_accession_id])
    response = login_test_client.get(
        f"/search/feature/accession/{private_feature.accession_id}?accept=application/json"
    ).request(id_view, id_type="accession", feature_id=private_feature.accession_id)
    assert response.status_code == 200


def test_get_feature_accession_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None

    group_login_test_client.set_group_experiments([private_feature.experiment_accession_id])
    response = group_login_test_client.get(
        f"/search/feature/accession/{private_feature.accession_id}?accept=application/json"
    ).request(id_view, id_type="accession", feature_id=private_feature.accession_id)
    assert response.status_code == 200


def test_get_archived_feature_accession_with_anonymous_client(
    public_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        public_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}?accept=application/json"
        ).request(id_view, id_type="accession", feature_id=archived_feature.accession_id)


def test_get_archived_feature_accession_with_authenticated_client(
    login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}?accept=application/json"
        ).request(id_view, id_type="accession", feature_id=archived_feature.accession_id)


def test_get_archived_feature_accession_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None
    login_test_client.set_user_experiments([archived_feature.experiment_accession_id])
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}?accept=application/json"
        ).request(id_view, id_type="accession", feature_id=archived_feature.accession_id)


def test_get_archived_feature_accessionl_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None
    group_login_test_client.set_group_experiments([cast(str, archived_feature.experiment_accession_id)])

    with pytest.raises(PermissionDenied):
        group_login_test_client.get(
            f"/search/feature/accession/{archived_feature.accession_id}?accept=application/json"
        ).request(id_view, id_type="accession", feature_id=archived_feature.accession_id)


def test_get_feature_name_json(public_test_client: RequestBuilder, id_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/feature/name/{quote_plus(feature.name)}?accept=application/json"
    ).request(id_view, id_type="name", feature_id=feature.name)
    check_json_response(response, feature)


def test_get_feature_name_html(public_test_client: RequestBuilder, id_view, feature: DNAFeature):
    response = public_test_client.get(f"/search/feature/name/{quote_plus(feature.name)}").request(
        id_view, id_type="name", feature_id=feature.name
    )

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_get_no_feature_name_html(public_test_client: RequestBuilder, id_view):
    with pytest.raises(Http404):
        public_test_client.get("/search/feature/name/BRCA2").request(id_view, id_type="name", feature_id="BRCA2")


def test_get_feature_name_with_anonymous_client(
    public_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    response = public_test_client.get(
        f"/search/feature/name/{quote_plus(private_feature.name)}?accept=application/json"
    ).request(id_view, id_type="name", feature_id=private_feature.name)
    assert response.status_code == 302


def test_get_feature_name_with_authenticated_client(
    login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/name/{quote_plus(private_feature.name)}?accept=application/json"
        ).request(id_view, id_type="name", feature_id=private_feature.name)


def test_get_feature_name_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None
    login_test_client.set_user_experiments([private_feature.experiment_accession_id])

    response = login_test_client.get(
        f"/search/feature/name/{quote_plus(private_feature.name)}?accept=application/json"
    ).request(id_view, id_type="name", feature_id=private_feature.name)
    assert response.status_code == 200


def test_get_feature_name_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, id_view, private_feature: DNAFeature
):
    assert private_feature.experiment_accession_id is not None
    group_login_test_client.set_group_experiments([private_feature.experiment_accession_id])

    response = group_login_test_client.get(
        f"/search/feature/name/{quote_plus(private_feature.name)}?accept=application/json"
    ).request(id_view, id_type="name", feature_id=private_feature.name)
    assert response.status_code == 200


def test_get_archived_feature_name_with_anonymous_client(
    public_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        public_test_client.get(
            f"/search/feature/name/{quote_plus(archived_feature.name)}?accept=application/json"
        ).request(id_view, id_type="name", feature_id=archived_feature.name)


def test_get_archived_feature_name_with_authenticated_client(
    login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/name/{quote_plus(archived_feature.name)}?accept=application/json"
        ).request(id_view, id_type="name", feature_id=archived_feature.name)


def test_get_archived_feature_name_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None
    login_test_client.set_user_experiments([archived_feature.experiment_accession_id])

    with pytest.raises(PermissionDenied):
        login_test_client.get(
            f"/search/feature/name/{quote_plus(archived_feature.name)}?accept=application/json"
        ).request(id_view, id_type="name", feature_id=archived_feature.name)


def test_get_archived_feature_name_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, id_view, archived_feature: DNAFeature
):
    assert archived_feature.experiment_accession_id is not None
    group_login_test_client.set_group_experiments([archived_feature.experiment_accession_id])

    with pytest.raises(PermissionDenied):
        group_login_test_client.get(
            f"/search/feature/name/{quote_plus(archived_feature.name)}?accept=application/json"
        ).request(id_view, id_type="name", feature_id=archived_feature.name)


def test_get_feature_loc_e2e(client: Client, feature: DNAFeature):
    response = client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper + 10}?accept=application/json"  # noqa: E501
    )
    check_json_response(response, feature)


def test_get_feature_loc_tsv(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper + 10}?accept=text/tab-separated-values"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower - 10, end=feature.location.upper + 10)
    check_tsv_response(response, feature)


def test_get_feature_loc_bed(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper + 10}?accept=text/tab-separated-values&tsv_format=bed6"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower - 10, end=feature.location.upper + 10)
    check_bed_response(response, feature)


def test_get_feature_loc_html(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper + 10}"
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower - 10, end=feature.location.upper + 10)

    # The content of the page isn't necessarily stable, so we just want to make sure
    # we don't get a 400 or 500 error here
    assert response.status_code == 200


def test_get_feature_loc_with_anonymous_client(
    public_test_client: RequestBuilder, loc_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    response = public_test_client.get(
        f"/search/featureloc/{pub_feature.chrom_name}/{pub_feature.location.lower - 10}/{archived_feature.location.upper + 10}?accept=application/json"  # noqa: E501
    ).request(
        loc_view,
        chromo=pub_feature.chrom_name,
        start=pub_feature.location.lower - 10,
        end=archived_feature.location.upper + 10,
    )
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content) == 1


def test_get_feature_loc_with_authenticated_client(
    login_test_client: RequestBuilder, loc_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, _private_feature, archived_feature = nearby_feature_mix
    response = login_test_client.get(
        f"/search/featureloc/{pub_feature.chrom_name}/{pub_feature.location.lower - 10}/{archived_feature.location.upper + 10}?accept=application/json"  # noqa: E501
    ).request(
        loc_view,
        chromo=pub_feature.chrom_name,
        start=pub_feature.location.lower - 10,
        end=archived_feature.location.upper + 10,
    )
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content) == 1


def test_get_feature_loc_with_authenticated_authorized_client(
    login_test_client: RequestBuilder, loc_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
):
    pub_feature, private_feature, archived_feature = nearby_feature_mix

    login_test_client.set_user_experiments(
        [private_feature.experiment_accession_id, archived_feature.experiment_accession_id]
    )
    response = login_test_client.get(
        f"/search/featureloc/{pub_feature.chrom_name}/{pub_feature.location.lower - 10}/{archived_feature.location.upper + 10}?accept=application/json"  # noqa: E501
    ).request(
        loc_view,
        chromo=pub_feature.chrom_name,
        start=pub_feature.location.lower - 10,
        end=archived_feature.location.upper + 10,
    )
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content) == 2


def test_get_feature_loc_with_authenticated_authorized_group_client(
    group_login_test_client: RequestBuilder, loc_view, nearby_feature_mix: tuple[DNAFeature, DNAFeature, DNAFeature]
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
        f"/search/featureloc/{pub_feature.chrom_name}/{pub_feature.location.lower - 10}/{archived_feature.location.upper + 10}?accept=application/json"  # noqa: E501
    ).request(
        loc_view,
        chromo=pub_feature.chrom_name,
        start=pub_feature.location.lower - 10,
        end=archived_feature.location.upper + 10,
    )
    assert response.status_code == 200

    json_content = response.json()
    assert len(json_content) == 2


def test_get_feature_loc_implicit_overlap_json(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper - 10}?accept=application/json"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower - 10, end=feature.location.upper - 10)
    check_json_response(response, feature)


def test_get_feature_loc_explicit_overlap_json(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper - 10}?accept=application/json&search_type=overlap"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower - 10, end=feature.location.upper - 10)
    check_json_response(response, feature)


def test_get_feature_loc_no_overlap_json(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.upper + 10}/{feature.location.upper + 20}?accept=application/json"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.upper + 10, end=feature.location.upper + 20)

    assert response.status_code == 200
    json_content = response.json()
    assert isinstance(json_content, list)
    assert len(json_content) == 0


def test_get_feature_loc_exact_json(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower}/{feature.location.upper}?accept=application/json&search_type=exact"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower, end=feature.location.upper)
    check_json_response(response, feature)


def test_get_feature_loc_not_exact_json(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower}/{feature.location.upper + 20}?accept=application/json&search_type=exact"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower, end=feature.location.upper + 20)

    assert response.status_code == 200
    json_content = response.json()
    assert isinstance(json_content, list)
    assert len(json_content) == 0


def test_get_feature_loc_feature_type_json(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper + 10}?accept=application/json&feature_type={feature.get_feature_type_display()}"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower - 10, end=feature.location.upper + 10)

    check_json_response(response, feature)


def test_get_feature_loc_not_feature_type_json(public_test_client: RequestBuilder, loc_view, feature: DNAFeature):
    not_feature_type = [f for f in DNAFeatureType if str(f) != feature.feature_type][0]
    response = public_test_client.get(
        f"/search/featureloc/{feature.chrom_name}/{feature.location.lower - 10}/{feature.location.upper + 10}?accept=application/json&feature_type={not_feature_type.value}"  # noqa: E501
    ).request(loc_view, chromo=feature.chrom_name, start=feature.location.lower - 10, end=feature.location.upper + 10)

    assert response.status_code == 200
    json_content = response.json()
    assert isinstance(json_content, list)
    assert len(json_content) == 0
