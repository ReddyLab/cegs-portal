import sys
from functools import lru_cache

from cegs_portal.search.models import DNAFeature, DNAFeatureType


@lru_cache(maxsize=1)
def get_pos_genes(chrom_name, ref_genome):
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
def get_neg_genes(chrom_name, ref_genome):
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


def find_pos_closest(midpoint, genes):
    if len(genes) == 0:
        return None

    start = 0
    end = len(genes)
    index = (end + start) // 2
    while True:
        gene = genes[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest feature.
            for i in range(-6, 7):
                new_gene = genes[min(max(0, index + i), len(genes) - 1)]
                if abs(new_gene["location"].lower - midpoint) < abs(gene["location"].lower - midpoint):
                    gene = new_gene
            return gene

        if gene["location"].lower >= midpoint:
            end = index
        elif gene["location"].lower < midpoint:
            start = index

        index = (end + start) // 2


def find_neg_closest(midpoint, genes):
    if len(genes) == 0:
        return None

    start = 0
    end = len(genes)
    index = (end + start) // 2
    while True:
        gene = genes[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest feature.
            for i in range(-6, 7):
                new_gene = genes[min(max(0, index + i), len(genes) - 1)]
                if abs(new_gene["location"].upper - midpoint) < abs(gene["location"].upper - midpoint):
                    gene = new_gene
            return gene

        if gene["location"].upper >= midpoint:
            end = index
        elif gene["location"].upper < midpoint:
            start = index

        index = (end + start) // 2


def get_closest_gene(ref_genome, chrom_name, start, end):
    range_midpoint = (start + end) // 2

    closest_pos_gene = find_pos_closest(range_midpoint, get_pos_genes(chrom_name, ref_genome))
    pos_feature_distance = (
        range_midpoint - closest_pos_gene["location"].lower if closest_pos_gene is not None else sys.maxsize
    )
    closest_neg_gene = find_neg_closest(range_midpoint, get_neg_genes(chrom_name, ref_genome))
    neg_feature_distance = (
        range_midpoint - closest_neg_gene["location"].upper if closest_neg_gene is not None else sys.maxsize
    )

    closest_gene = None
    distance = None
    gene_name = "No Gene"

    if closest_pos_gene is None and closest_neg_gene is None:
        pass
    elif closest_pos_gene is None or abs(neg_feature_distance) < abs(pos_feature_distance):
        closest_gene = closest_neg_gene
        distance = neg_feature_distance
    elif closest_neg_gene is None or abs(pos_feature_distance) <= abs(neg_feature_distance):
        closest_gene = closest_pos_gene
        distance = pos_feature_distance

    if closest_gene is not None:
        gene_name = closest_gene["name"]

    return closest_gene, distance, gene_name
