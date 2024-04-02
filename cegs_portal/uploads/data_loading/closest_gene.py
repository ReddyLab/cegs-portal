from functools import lru_cache

from cegs_portal.search.models import DNAFeature, DNAFeatureType


@lru_cache(maxsize=1)
def get_pos_features(chrom_name, ref_genome):
    return list(
        DNAFeature.objects.filter(
            chrom_name=chrom_name,
            strand="+",
            ref_genome=ref_genome,
            feature_type=DNAFeatureType.GENE,
        )
        .order_by("location")
        .values("id", "name", "location", "ensembl_id")
        .all()
    )


@lru_cache(maxsize=1)
def get_neg_features(chrom_name, ref_genome):
    return list(
        DNAFeature.objects.filter(
            chrom_name=chrom_name,
            strand="-",
            ref_genome=ref_genome,
            feature_type=DNAFeatureType.GENE,
        )
        .order_by("location")
        .values("id", "name", "location", "ensembl_id")
        .all()
    )


def find_pos_closest(dhs_midpoint, features):
    if len(features) == 0:
        return None

    start = 0
    end = len(features)
    index = (end + start) // 2
    while True:
        feature = features[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest feature.
            for i in range(-6, 7):
                new_feature = features[min(max(0, index + i), len(features) - 1)]
                if abs(new_feature["location"].lower - dhs_midpoint) < abs(feature["location"].lower - dhs_midpoint):
                    feature = new_feature
            return feature

        if feature["location"].lower >= dhs_midpoint:
            end = index
        elif feature["location"].lower < dhs_midpoint:
            start = index

        index = (end + start) // 2


def find_neg_closest(dhs_midpoint, features):
    if len(features) == 0:
        return None

    start = 0
    end = len(features)
    index = (end + start) // 2
    while True:
        feature = features[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest feature.
            for i in range(-6, 7):
                new_feature = features[min(max(0, index + i), len(features) - 1)]
                if abs(new_feature["location"].upper - dhs_midpoint) < abs(feature["location"].upper - dhs_midpoint):
                    feature = new_feature
            return feature

        if feature["location"].upper >= dhs_midpoint:
            end = index
        elif feature["location"].upper < dhs_midpoint:
            start = index

        index = (end + start) // 2


def get_closest_gene(ref_genome, chrom_name, start, end):
    range_midpoint = (start + end) // 2
    closest_pos_feature = find_pos_closest(range_midpoint, get_pos_features(chrom_name, ref_genome))

    closest_neg_feature = find_neg_closest(range_midpoint, get_neg_features(chrom_name, ref_genome))

    if closest_pos_feature is None and closest_neg_feature is None:
        closest_feature = None
        distance = -1
        gene_name = "No Gene"
    elif closest_pos_feature is None:
        closest_feature = closest_neg_feature
        distance = abs(range_midpoint - closest_neg_feature["location"].upper)
    elif closest_neg_feature is None or abs(range_midpoint - closest_pos_feature["location"].lower) <= abs(
        closest_neg_feature["location"].upper - range_midpoint
    ):
        closest_feature = closest_pos_feature
        distance = abs(range_midpoint - closest_pos_feature["location"].lower)
    else:
        closest_feature = closest_neg_feature
        distance = abs(closest_neg_feature["location"].upper - range_midpoint)

    if closest_feature is not None:
        gene_name = closest_feature["name"]

    return closest_feature, distance, gene_name
