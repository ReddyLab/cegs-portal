from typing import Iterable

import pytest

from cegs_portal.search.json_templates.v1.features import assembly as a_json
from cegs_portal.search.json_templates.v1.features import feature as f_json
from cegs_portal.search.json_templates.v1.features import feature_assemblies as fa_json
from cegs_portal.search.json_templates.v1.features import features as fs_json
from cegs_portal.search.models import Feature, FeatureAssembly

pytestmark = pytest.mark.django_db


def test_feature_assemblies(feature_assemblies: Iterable[FeatureAssembly]):
    feature_dict = {}
    for a in feature_assemblies:
        a_list = feature_dict.get(a.feature, [])
        a_list.append(a)
        feature_dict[a.feature] = a_list

    result = [
        {
            "feature": f_json(f),
            "assemblies": [a_json(a) for a in a_list],
        }
        for f, a_list in feature_dict.items()
    ]

    assert fa_json(feature_assemblies) == result

    result = [
        {
            "feature": f_json(f, json_format="genoverse"),
            "assemblies": [a_json(a, json_format="genoverse") for a in a_list],
        }
        for f, a_list in feature_dict.items()
    ]

    assert fa_json(feature_assemblies, json_format="genoverse") == result


def test_features(features: Iterable[Feature]):
    result = [
        {
            "feature": f_json(f),
            "assemblies": [a_json(a) for a in f.assemblies.all()],
        }
        for f in features
    ]

    assert fs_json(features) == result

    result = [
        {
            "feature": f_json(f, json_format="genoverse"),
            "assemblies": [a_json(a, json_format="genoverse") for a in f.assemblies.all()],
        }
        for f in features
    ]

    assert fs_json(features, json_format="genoverse") == result


def test_feature(feature: Feature):
    result = {
        "id": feature.id,
        "ensembl_id": feature.ensembl_id,
        "type": feature.feature_type,
        "subtype": feature.feature_subtype,
        "parent_id": feature.parent.id if feature.parent is not None else None,
    }
    assert f_json(feature) == result

    result["id"] = str(feature.id)
    assert f_json(feature, json_format="genoverse") == result


def test_assembly(assembly: FeatureAssembly):
    result = {
        "id": assembly.id,
        "chr": assembly.chrom_name,
        "name": assembly.name,
        "start": assembly.location.lower,
        "end": assembly.location.upper - 1,
        "strand": assembly.strand,
        "ids": assembly.ids,
        "ref_genome": assembly.ref_genome,
        "ref_genome_patch": assembly.ref_genome_patch,
    }
    assert a_json(assembly) == result

    result["id"] = str(assembly.id)
    result["chr"] = assembly.chrom_name.removeprefix("chr")
    assert a_json(assembly, json_format="genoverse") == result
