from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.dna_features import feature as f_json
from cegs_portal.search.json_templates.v1.dna_features import features as fs_json
from cegs_portal.search.models import DNAFeature

pytestmark = pytest.mark.django_db


def test_features(features: Iterable[DNAFeature]):
    result = [f_json(a) for a in features]

    assert fs_json(features) == result

    result = [f_json(a, {"json_format": "genoverse"}) for a in features]

    assert fs_json(features, {"json_format": "genoverse"}) == result


def test_feature(feature: DNAFeature):
    result = {
        "id": feature.id,
        "accession_id": feature.accession_id,
        "ensembl_id": feature.ensembl_id,
        "closest_gene_name": feature.closest_gene_name,
        "closest_gene_ensembl_id": None,
        "cell_line": feature.cell_line,
        "chr": feature.chrom_name,
        "name": feature.name,
        "start": feature.location.lower,
        "end": feature.location.upper - 1,
        "strand": feature.strand,
        "ids": feature.ids,
        "type": feature.get_feature_type_display(),
        "subtype": feature.feature_subtype,
        "ref_genome": feature.ref_genome,
        "ref_genome_patch": feature.ref_genome_patch,
        "parent_id": feature.parent_id if feature.parent is not None else None,
        "misc": feature.misc,
    }
    if feature.closest_gene is not None:
        result["closest_gene_ensembl_id"] = feature.closest_gene.ensembl_id

    assert f_json(feature) == result

    result["id"] = str(feature.id)
    result["chr"] = feature.chrom_name.removeprefix("chr")
    assert f_json(feature, {"json_format": "genoverse"}) == result
