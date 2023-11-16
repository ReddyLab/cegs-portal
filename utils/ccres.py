import csv
from collections import defaultdict

from psycopg2.extras import NumericRange

from cegs_portal.search.models import AccessionType, DNAFeature, DNAFeatureType


def get_ccre(loc: tuple[str, int, int, str]):
    chrom, start, end, ref_genome = loc
    return DNAFeature.objects.get(
        chrom_name=chrom,
        location=NumericRange(start, end, "[)"),
        ref_genome=ref_genome,
        feature_type=DNAFeatureType.CCRE,
    )


def source_ccre_locs(closest_ccre_filename, ref_genome):
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


def save_ccres(closest_ccre_filename, sources, ref_genome, accession_ids):
    source_ccres = source_ccre_locs(closest_ccre_filename, ref_genome)
    for source in sources:
        ccres = source_ccres[(source.chrom_name, source.location.lower, source.location.upper)]
        if len(ccres) > 0:
            source.associated_ccres.add(*[get_ccre(ccre) for ccre in ccres])
        else:
            ccre = DNAFeature(
                accession_id=accession_ids.incr(AccessionType.CCRE),
                cell_line=source.cell_line,
                chrom_name=source.chrom_name,
                closest_gene=source.closest_gene,
                closest_gene_distance=source.closest_gene_distance,
                closest_gene_name=source.closest_gene_name,
                closest_gene_ensembl_id=source.closest_gene_ensembl_id,
                location=source.location,
                ref_genome=source.ref_genome,
                ref_genome_patch=source.ref_genome_patch,
                feature_type=DNAFeatureType.CCRE,
                source_file=source.source_file,
                misc={"pseudo": True},
            )
            ccre.save()
            source.associated_ccres.add(ccre)
