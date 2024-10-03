import pytest

from cegs_portal.search.models import DNAFeature, DNAFeatureType
from cegs_portal.uploads.data_loading.experiment import Experiment, FeatureRow
from cegs_portal.uploads.data_loading.types import (
    ChromosomeStrands,
    Facets,
    FeatureType,
    GenomeAssembly,
    GrnaFacet,
)

pytestmark = pytest.mark.django_db


def ccre_ids():
    return set(DNAFeature.objects.filter(feature_type=DNAFeatureType.CCRE).values_list("id", flat=True))


def generated_features():
    return DNAFeature.objects.exclude(feature_type__in=[DNAFeatureType.CCRE, DNAFeatureType.GENE]).all()


def test_ccre_associations(experiment_metadata):
    features = [
        FeatureRow(
            name="0",
            chrom_name="chr1",
            location=(0, 10),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            misc={"grna": "0"},
        ),
        FeatureRow(
            name="1",
            chrom_name="chr1",
            location=(90, 120),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            misc={"grna": "1"},
        ),
        FeatureRow(
            name="2",
            chrom_name="chr1",
            location=(290, 410),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            misc={"grna": "1"},
        ),
        FeatureRow(
            name="3",
            chrom_name="chr1",
            location=(510, 590),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            misc={"grna": "1"},
        ),
        FeatureRow(
            name="4",
            chrom_name="chr1",
            location=(940, 950),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            misc={"grna": "2"},
        ),
    ]

    old_ids = ccre_ids()

    experiment = Experiment(experiment_metadata)
    experiment.features = features
    experiment.save()

    overlap_ccre_count = 0

    for feature in generated_features():
        for ccre in [ccre for ccre in feature.associated_ccres.all()]:
            if ccre.id in old_ids:
                assert ccre.misc.get("pseudo") is None
                overlap_ccre_count += 1
            else:
                assert ccre.misc["pseudo"]

    assert overlap_ccre_count == 3


def test_close_ccre_associations(experiment_metadata):
    # Make sure the algorithm works correctly for features that abut existing cCREs
    # Neither of these features should "overlap" so they should both result in
    # two new pseudo cCREs

    features = [
        FeatureRow(
            name="0",
            chrom_name="chr1",
            location=(90, 100),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            misc={"grna": "0"},
        ),
        FeatureRow(
            name="1",
            chrom_name="chr1",
            location=(200, 220),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            misc={"grna": "1"},
        ),
    ]

    old_ids = ccre_ids()

    experiment = Experiment(experiment_metadata)
    experiment.features = features
    experiment.save()

    for feature in generated_features():
        for ccre in [ccre for ccre in feature.associated_ccres.all()]:
            assert ccre.id not in old_ids


def test_parent_ccre_associations(experiment_metadata):
    parent_features = [
        FeatureRow(
            name="a",
            chrom_name="chr1",
            location=(0, 50),
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.DHS,
        ),
        FeatureRow(
            name="b",
            chrom_name="chr1",
            location=(90, 190),
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.DHS,
        ),
        FeatureRow(
            name="c",
            chrom_name="chr1",
            location=(210, 290),
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.DHS,
        ),
    ]
    features = [
        FeatureRow(
            name="0",
            chrom_name="chr1",
            location=(5, 10),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            parent_name="a",
            misc={"grna": "0"},
        ),
        FeatureRow(
            name="1",
            chrom_name="chr1",
            location=(15, 25),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            parent_name="a",
            misc={"grna": "1"},
        ),
        FeatureRow(
            name="2",
            chrom_name="chr1",
            location=(30, 40),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            parent_name="a",
            misc={"grna": "2"},
        ),
        FeatureRow(
            name="3",
            chrom_name="chr1",
            location=(91, 99),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            parent_name="b",
            misc={"grna": "3"},
        ),
        FeatureRow(
            name="4",
            chrom_name="chr1",
            location=(120, 130),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            parent_name="b",
            misc={"grna": "4"},
        ),
        FeatureRow(
            name="5",
            chrom_name="chr1",
            location=(120, 130),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            parent_name="c",
            misc={"grna": "5"},
        ),
        FeatureRow(
            name="6",
            chrom_name="chr1",
            location=(120, 130),
            strand=ChromosomeStrands.POSITIVE,
            genome_assembly=GenomeAssembly.HG38,
            cell_line="iPSC",
            feature_type=FeatureType.GRNA,
            facets=[(Facets.GRNA_TYPE, GrnaFacet.TARGETING)],
            parent_name="c",
            misc={"grna": "6"},
        ),
    ]

    old_ids = ccre_ids()
    new_ccre_ids = set()

    experiment = Experiment(experiment_metadata)
    experiment.features = features
    experiment.parent_features = parent_features
    experiment.save()

    overlap_ccre_count = 0
    non_overlap_ccre_count = 0

    assert len(generated_features()) == 10

    for feature in generated_features():
        for ccre in [ccre for ccre in feature.associated_ccres.all()]:
            if ccre.id in old_ids:
                assert ccre.misc.get("pseudo") is None
                overlap_ccre_count += 1
            else:
                new_ccre_ids.add(ccre.id)
                assert ccre.misc["pseudo"]
                non_overlap_ccre_count += 1

    assert overlap_ccre_count == 3
    assert non_overlap_ccre_count == 7
    assert len(new_ccre_ids) == 2
