from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.features import assembly as a_json
from cegs_portal.search.json_templates.v1.features import feature_assemblies as fa_json
from cegs_portal.search.models import FeatureAssembly

pytestmark = pytest.mark.django_db


def test_feature_assemblies(feature_assemblies: Iterable[FeatureAssembly]):
    result = [a_json(a) for a in feature_assemblies]

    assert fa_json(feature_assemblies) == result

    result = [a_json(a, json_format="genoverse") for a in feature_assemblies]

    assert fa_json(feature_assemblies, json_format="genoverse") == result


def test_assembly(assembly: FeatureAssembly):
    result = {
        "id": assembly.id,
        "ensembl_id": assembly.ensembl_id,
        "chr": assembly.chrom_name,
        "name": assembly.name,
        "start": assembly.location.lower,
        "end": assembly.location.upper - 1,
        "strand": assembly.strand,
        "ids": assembly.ids,
        "type": assembly.feature_type,
        "subtype": assembly.feature_subtype,
        "ref_genome": assembly.ref_genome,
        "ref_genome_patch": assembly.ref_genome_patch,
        "parent_id": assembly.parent.id if assembly.parent is not None else None,
    }
    assert a_json(assembly) == result

    result["id"] = str(assembly.id)
    result["chr"] = assembly.chrom_name.removeprefix("chr")
    assert a_json(assembly, json_format="genoverse") == result
