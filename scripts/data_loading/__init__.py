from functools import lru_cache

from cegs_portal.search.models import FeatureAssembly


def check_genome(ref_genome: str, ref_genome_patch: str):
    if len(ref_genome) == 0:
        raise ValueError(f"reference genome '{ref_genome}'must not be blank")

    if not ((ref_genome_patch.isascii() and ref_genome_patch.isdigit()) or len(ref_genome_patch) == 0):
        raise ValueError(f"reference genome patch '{ref_genome_patch}' must be either blank or a series of digits")


@lru_cache(maxsize=1)
def get_pos_assemblies(chrom_name, ref_genome):
    return list(
        FeatureAssembly.objects.filter(
            chrom_name=chrom_name,
            strand="+",
            ref_genome=ref_genome,
            feature_type="gene",
        )
        .order_by("location")
        .all()
    )


@lru_cache(maxsize=1)
def get_neg_assemblies(chrom_name, ref_genome):
    return list(
        FeatureAssembly.objects.filter(
            chrom_name=chrom_name,
            strand="-",
            ref_genome=ref_genome,
            feature_type="gene",
        )
        .order_by("location")
        .all()
    )


def find_pos_closest(dhs_midpoint, assemblies):
    start = 0
    end = len(assemblies)
    index = (end + start) // 2
    while True:
        assembly = assemblies[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest assembly.
            for i in range(-6, 7):
                new_assembly = assemblies[min(max(0, index + i), len(assemblies) - 1)]
                if abs(new_assembly.location.lower - dhs_midpoint) < abs(assembly.location.lower - dhs_midpoint):
                    assembly = new_assembly
            return assembly

        if assembly.location.lower >= dhs_midpoint:
            end = index
        elif assembly.location.lower < dhs_midpoint:
            start = index

        index = (end + start) // 2


def find_neg_closest(dhs_midpoint, assemblies):
    start = 0
    end = len(assemblies)
    index = (end + start) // 2
    while True:
        assembly = assemblies[index]
        if index == end or index == start:
            # the loop is hacky, but the binary search only gets _close_ to finding the closest assembly.
            for i in range(-6, 7):
                new_assembly = assemblies[min(max(0, index + i), len(assemblies) - 1)]
                if abs(new_assembly.location.upper - dhs_midpoint) < abs(assembly.location.upper - dhs_midpoint):
                    assembly = new_assembly
            return assembly

        if assembly.location.upper >= dhs_midpoint:
            end = index
        elif assembly.location.upper < dhs_midpoint:
            start = index

        index = (end + start) // 2


def get_closest_gene(ref_genome, chrom_name, start, end):
    range_midpoint = (start + end) // 2
    closest_pos_assembly = find_pos_closest(range_midpoint, get_pos_assemblies(chrom_name, ref_genome))

    closest_neg_assembly = find_neg_closest(range_midpoint, get_neg_assemblies(chrom_name, ref_genome))

    if closest_pos_assembly is None and closest_neg_assembly is None:
        closest_assembly = None
        distance = -1
        gene_name = "No Gene"
    elif closest_pos_assembly is None:
        closest_assembly = closest_neg_assembly
        distance = abs(range_midpoint - closest_neg_assembly.location.upper)
    elif closest_neg_assembly is None or abs(range_midpoint - closest_pos_assembly.location.lower) <= abs(
        closest_neg_assembly.location.upper - range_midpoint
    ):
        closest_assembly = closest_pos_assembly
        distance = abs(range_midpoint - closest_pos_assembly.location.lower)
    else:
        closest_assembly = closest_neg_assembly
        distance = abs(closest_neg_assembly.location.upper - range_midpoint)

    if closest_assembly is not None:
        gene_name = closest_assembly.name

    return closest_assembly, distance, gene_name
