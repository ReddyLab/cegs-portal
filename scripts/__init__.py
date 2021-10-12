def check_genome(ref_genome: str, ref_genome_patch: str):
    if len(ref_genome) == 0:
        raise ValueError(f"reference genome '{ref_genome}'must not be blank")

    if not ((ref_genome_patch.isascii() and ref_genome_patch.isdigit()) or len(ref_genome_patch) == 0):
        raise ValueError(f"reference genome patch '{ref_genome_patch}' must be either blank or a series of digits")
