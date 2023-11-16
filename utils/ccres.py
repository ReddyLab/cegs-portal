import csv
from collections import defaultdict

from psycopg2.extras import NumericRange

from cegs_portal.search.models import DNAFeature, DNAFeatureType


def get_ccre(loc: tuple[str, int, int, str]):
    chrom, start, end, ref_genome = loc
    return DNAFeature.objects.get(
        chrom_name=chrom,
        location=NumericRange(start, end, "[]"),
        ref_genome=ref_genome,
        feature_type=DNAFeatureType.CCRE,
    )


def dhs_ccre_locs(closest_ccre_filename, ref_genome):
    ccres = defaultdict(lambda: [])
    with open(closest_ccre_filename, "r") as closest_ccres:
        ccre_reader = csv.reader(closest_ccres, delimiter="\t")
        for source_chr, source_start, source_end, ccre_chr, ccre_start, ccre_end, _, _, _ in ccre_reader:
            source_start = int(source_start)
            source_end = int(source_end)
            ccre_start = int(ccre_start)
            ccre_end = int(ccre_end)
            ccres[(source_chr, source_start, source_end)].append((ccre_chr, ccre_start, ccre_end, ref_genome))

    return ccres


def save_ccres(closest_ccre_filename, dhss, ref_genome):
    dhs_ccres = dhs_ccre_locs(closest_ccre_filename, ref_genome)
    for dhs in dhss:
        ccres = dhs_ccres[(dhs.chrom_name, dhs.location.lower, dhs.location.upper)]
        if len(ccres) > 0:
            dhs.associated_ccres.add(*[get_ccre(ccre) for ccre in ccres])
