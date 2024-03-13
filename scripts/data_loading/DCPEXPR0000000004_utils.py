from .types import ChromosomeStrands, RangeBounds


def grna_loc(line):
    grna_id = line["grna"]
    grna_type = line["type"]
    grna_info = grna_id.split("-")
    if len(grna_info) == 5:
        chrom_name, grna_start_str, grna_end_str, grna_strand, _grna_seq = grna_info
        if grna_strand == "+":
            grna_strand = ChromosomeStrands.POSITIVE
    elif len(grna_info) == 6:
        chrom_name, grna_start_str, grna_end_str, _x, _y, _grna_seq = grna_info
        grna_strand = ChromosomeStrands.NEGATIVE

    if grna_type == "targeting":
        grna_start = int(grna_start_str)
        grna_end = int(grna_end_str)
    else:
        if grna_strand == ChromosomeStrands.POSITIVE:
            grna_start = int(grna_start_str)
            grna_end = int(grna_start_str) + 20
        elif grna_strand == ChromosomeStrands.NEGATIVE:
            grna_start = int(grna_end_str) - 20
            grna_end = int(grna_end_str)

    if grna_strand == ChromosomeStrands.POSITIVE:
        grna_bounds = RangeBounds.HALF_OPEN_RIGHT
    elif grna_strand == ChromosomeStrands.NEGATIVE:
        grna_bounds = RangeBounds.HALF_OPEN_LEFT

    return chrom_name, grna_start, grna_end, grna_bounds, grna_strand
