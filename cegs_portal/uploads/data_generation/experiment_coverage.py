import os
from subprocess import run

from cegs_portal.search.models import (
    Analysis,
    EffectObservationDirectionType,
    FacetValue,
)


def gen_coverage(analysis: Analysis, analysis_dir: str, bin_size=2_000_000, chrom_name=None):
    args = ["cov_viz", analysis_dir, analysis.accession_id, analysis.genome_assembly.upper(), str(bin_size)]

    if chrom_name is not None:
        args.append(chrom_name)

    run(
        args,
        check=True,
        env={"PATH": os.getenv("PATH"), "DATABASE_URL": os.getenv("DATABASE_URL")},
    )


def gen_coverage_manifest(analysis: Analysis, analysis_dir: str):
    default_facet_ids = (
        FacetValue.objects.filter(
            value__in=[
                EffectObservationDirectionType.DEPLETED.value,
                EffectObservationDirectionType.ENRICHED.value,
                EffectObservationDirectionType.BOTH.value,
            ]
        )
        .all()
        .values_list("id", flat=True)
    )

    args = [
        "cov_viz_manifest",
        analysis.genome_assembly.upper(),
        os.path.join(analysis_dir, "level1.ecd"),
        analysis_dir,
        " ".join(str(f_id) for f_id in default_facet_ids),
    ]

    run(
        args,
        check=True,
        env={"PATH": os.getenv("PATH"), "DATABASE_URL": os.getenv("DATABASE_URL")},
    )
