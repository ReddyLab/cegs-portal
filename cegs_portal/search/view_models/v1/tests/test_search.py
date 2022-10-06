import pytest

from cegs_portal.search.models import ChromosomeLocation
from cegs_portal.search.models.utils import QueryToken
from cegs_portal.search.view_models.v1.search import (
    ParseWarning,
    SearchType,
    parse_query,
)


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
