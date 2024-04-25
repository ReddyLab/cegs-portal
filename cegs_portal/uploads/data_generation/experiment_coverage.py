import os
from subprocess import run

from cegs_portal.search.models import Analysis, FacetValue


def gen_coverage(analysis: Analysis, analysis_dir: str, bin_size=2_000_000, chrom_name=None):
    results = analysis.files.all()[0].data_file_info

    args = ["cov_viz", analysis_dir, analysis.accession_id, results.ref_genome.upper(), str(bin_size)]

    if chrom_name is not None:
        args.append(chrom_name)

    run(
        args,
        check=True,
        env={"PATH": os.getenv("PATH"), "DATABASE_URL": os.getenv("DATABASE_URL")},
    )


def gen_coverage_manifest(analysis: Analysis, analysis_dir: str):
    default_facet_ids = (
        FacetValue.objects.filter(value__in=["Depleted Only", "Enriched Only", "Mixed"])
        .all()
        .values_list("id", flat=True)
    )
    results = analysis.files.all()[0].data_file_info
    args = [
        "cov_viz_manifest",
        results.ref_genome.upper(),
        os.path.join(analysis_dir, "level1.ecd"),
        analysis_dir,
        " ".join(str(f_id) for f_id in default_facet_ids),
    ]

    run(
        args,
        check=True,
        env={"PATH": os.getenv("PATH"), "DATABASE_URL": os.getenv("DATABASE_URL")},
    )
