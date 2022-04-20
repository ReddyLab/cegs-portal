from django.db.models import F, IntegerField
from django.db.models.functions import Abs, Lower, Upper

from cegs_portal.search.models import FeatureAssembly


def check_genome(ref_genome: str, ref_genome_patch: str):
    if len(ref_genome) == 0:
        raise ValueError(f"reference genome '{ref_genome}'must not be blank")

    if not ((ref_genome_patch.isascii() and ref_genome_patch.isdigit()) or len(ref_genome_patch) == 0):
        raise ValueError(f"reference genome patch '{ref_genome_patch}' must be either blank or a series of digits")


def get_closest_gene(chrom_name, ref_genome, range_start, range_end):
    range_midpoint = (range_start + range_end) // 2

    closest_pos_assembly = (
        FeatureAssembly.objects.annotate(dist=Abs(Lower(F("location"), output_field=IntegerField()) - range_midpoint))
        .filter(chrom_name=chrom_name, strand="+", ref_genome=ref_genome, feature__feature_type="gene")
        .order_by("dist")
        .first()
    )

    closest_neg_assembly = (
        FeatureAssembly.objects.annotate(dist=Abs(Upper(F("location"), output_field=IntegerField()) - range_midpoint))
        .filter(chrom_name=chrom_name, strand="-", ref_genome=ref_genome, feature__feature_type="gene")
        .order_by("dist")
        .first()
    )

    if closest_pos_assembly is None:
        closest_assembly = closest_neg_assembly
    elif closest_neg_assembly is None:
        closest_assembly = closest_pos_assembly
    elif closest_pos_assembly.dist <= closest_neg_assembly.dist:
        closest_assembly = closest_pos_assembly
    else:
        closest_assembly = closest_neg_assembly

    if closest_assembly is not None:
        distance = closest_assembly.dist
        closest_gene = closest_assembly.feature
        gene_name = closest_assembly.name
    else:
        distance = -1
        closest_gene = None
        gene_name = "No Gene"

    return closest_gene, closest_assembly, distance, gene_name
