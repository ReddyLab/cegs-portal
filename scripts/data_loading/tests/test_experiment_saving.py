import pytest

from cegs_portal.search.models import DNAFeature, DNAFeatureType
from scripts.data_loading.types import FeatureType, GrnaFacet

pytestmark = pytest.mark.django_db


def ccre_ids():
    return set(DNAFeature.objects.filter(feature_type=DNAFeatureType.CCRE).values_list("id", flat=True))


def generated_features():
    return DNAFeature.objects.exclude(feature_type__in=[DNAFeatureType.CCRE, DNAFeatureType.GENE]).all()


def clean_features():
    for feature in generated_features():
        feature.delete()

    for ccre in DNAFeature.objects.filter(feature_type=DNAFeatureType.CCRE, misc__pseudo=True).all():
        ccre.delete()


@pytest.mark.usefixtures("ccres", "gene")
def test_ccre_associations(experiment_metadata):
    # This has to happen hear because load_experiment does DB calls on load
    # which isn't allowed in the pytest suite outside of tests with a django_db mark
    from scripts.data_loading.load_experiment import Experiment, FeatureRow

    def load_features(_):
        features = [
            FeatureRow(
                name="0",
                chrom_name="chr1",
                location=(0, 10, "[)"),
                strand="+",
                genome_assembly="GRCh38",
                cell_line="iPSC",
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                misc={"grna": "0"},
            ),
            FeatureRow(
                name="1",
                chrom_name="chr1",
                location=(90, 120, "[)"),
                strand="+",
                genome_assembly="GRCh38",
                cell_line="iPSC",
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                misc={"grna": "1"},
            ),
            FeatureRow(
                name="2",
                chrom_name="chr1",
                location=(290, 410, "[)"),
                strand="+",
                genome_assembly="GRCh38",
                cell_line="iPSC",
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                misc={"grna": "1"},
            ),
            FeatureRow(
                name="3",
                chrom_name="chr1",
                location=(510, 590, "[)"),
                strand="+",
                genome_assembly="GRCh38",
                cell_line="iPSC",
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                misc={"grna": "1"},
            ),
            FeatureRow(
                name="4",
                chrom_name="chr1",
                location=(940, 950, "[)"),
                strand="+",
                genome_assembly="GRCh38",
                cell_line="iPSC",
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                misc={"grna": "2"},
            ),
        ]
        return features, None

    old_ids = ccre_ids()

    Experiment(experiment_metadata).load(load_features).save()

    overlap_ccre_count = 0

    for feature in generated_features():
        for ccre in [ccre for ccre in feature.associated_ccres.all()]:
            if ccre.id in old_ids:
                assert ccre.misc.get("pseudo") is None
                overlap_ccre_count += 1
            else:
                assert ccre.misc["pseudo"]

    assert overlap_ccre_count == 3
    clean_features()

    assert len(generated_features()) == 0


@pytest.mark.usefixtures("ccres", "gene")
def test_close_ccre_associations(experiment_metadata):
    # Make sure the algorithm works correctly for features that abut existing cCREs
    # Neither of these features should "overlap" so they should both result in
    # two new pseudo cCREs

    # This has to happen hear because load_experiment does DB calls on load
    # which isn't allowed in the pytest suite outside of tests with a django_db mark
    from scripts.data_loading.load_experiment import Experiment, FeatureRow

    def load_features(_):
        features = [
            FeatureRow(
                name="0",
                chrom_name="chr1",
                location=(90, 100, "[)"),
                strand="+",
                genome_assembly="GRCh38",
                cell_line="iPSC",
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                misc={"grna": "0"},
            ),
            FeatureRow(
                name="1",
                chrom_name="chr1",
                location=(200, 220, "[)"),
                strand="+",
                genome_assembly="GRCh38",
                cell_line="iPSC",
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                misc={"grna": "1"},
            ),
        ]
        return features, None

    old_ids = ccre_ids()

    Experiment(experiment_metadata).load(load_features).save()

    for feature in generated_features():
        for ccre in [ccre for ccre in feature.associated_ccres.all()]:
            assert ccre.id not in old_ids

    clean_features()

    assert len(generated_features()) == 0
