import pytest

from cegs_portal.search.models import ChromosomeLocation
from cegs_portal.search.models.utils import QueryToken
from cegs_portal.search.view_models.v1.search import parse_query


@pytest.mark.parametrize(
    "query, result",
    [
        ("", ([], None, None)),
        ("hg38", ([], None, "GRCh38")),
        ("hg19", ([], None, "GRCh37")),
        ("chr1:1-100", ([], ChromosomeLocation("chr1", "1", "100"), None)),
        ("chr1:1-100 chr2: 2-200", ([], ChromosomeLocation("chr2", "2", "200"), None)),
        ("   chr1:1-100    chr2: 2-200   ", ([], ChromosomeLocation("chr2", "2", "200"), None)),
        ("   hg38   ", ([], None, "GRCh38")),
        ("   hg19 hg38   ", ([], None, "GRCh38")),
        ("DCPGENE00000000", ([QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, None)),
        ("DCPGENE00000000 hg19", ([QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37")),
        ("hg19 DCPGENE00000000", ([QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37")),
        ("   hg19    DCPGENE00000000    ", ([QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37")),
        ("   hg19    DCPGENE00000000    ", ([QueryToken.ACCESSION_ID.associate("DCPGENE00000000")], None, "GRCh37")),
        (
            "hg19 DCPGENE00000000 DCPGENE00000001",
            (
                [
                    QueryToken.ACCESSION_ID.associate("DCPGENE00000000"),
                    QueryToken.ACCESSION_ID.associate("DCPGENE00000001"),
                ],
                None,
                "GRCh37",
            ),
        ),
        (
            "hg19 DCPGENE00000000 ENSG00000001",
            (
                [QueryToken.ACCESSION_ID.associate("DCPGENE00000000"), QueryToken.ENSEMBL_ID.associate("ENSG00000001")],
                None,
                "GRCh37",
            ),
        ),
        (
            "DCPGENE00000000 hg19 ENSG00000001",
            (
                [QueryToken.ACCESSION_ID.associate("DCPGENE00000000"), QueryToken.ENSEMBL_ID.associate("ENSG00000001")],
                None,
                "GRCh37",
            ),
        ),
        (
            "hg19 chr1:1-100 DCPGENE00000000 ENSG00000001",
            (
                [QueryToken.ACCESSION_ID.associate("DCPGENE00000000"), QueryToken.ENSEMBL_ID.associate("ENSG00000001")],
                ChromosomeLocation("chr1", "1", "100"),
                "GRCh37",
            ),
        ),
        (
            " hg19 ENSG00000001   chr1:1-100 DCPGENE00000000 ",
            (
                [QueryToken.ENSEMBL_ID.associate("ENSG00000001"), QueryToken.ACCESSION_ID.associate("DCPGENE00000000")],
                ChromosomeLocation("chr1", "1", "100"),
                "GRCh37",
            ),
        ),
        (
            "hg19 chr1:1-100 BRCA2 DCPGENE00000000 ENSG00000001 CBX2",
            (
                [
                    QueryToken.GENE_NAME.associate("BRCA2"),
                    QueryToken.ACCESSION_ID.associate("DCPGENE00000000"),
                    QueryToken.ENSEMBL_ID.associate("ENSG00000001"),
                    QueryToken.GENE_NAME.associate("CBX2"),
                ],
                ChromosomeLocation("chr1", "1", "100"),
                "GRCh37",
            ),
        ),
        (
            "hg19 chr1:1-100 BRCA2 DCPGENE00000000 ENSG00000001 chr2:2-200 CBX2",
            (
                [
                    QueryToken.GENE_NAME.associate("BRCA2"),
                    QueryToken.ACCESSION_ID.associate("DCPGENE00000000"),
                    QueryToken.ENSEMBL_ID.associate("ENSG00000001"),
                    QueryToken.GENE_NAME.associate("CBX2"),
                ],
                ChromosomeLocation("chr2", "2", "200"),
                "GRCh37",
            ),
        ),
    ],
)
def test_parse_query(query, result):
    assert parse_query(query) == result
