import os
import shutil
from subprocess import CalledProcessError, run

from django.contrib.staticfiles import finders

from cegs_portal.search.models import Analysis, FacetValue


def analysis_dir(analysis):
    experiment = analysis.experiment_id
    experiment_path = finders.find(f"search/experiments/{experiment}")
    if experiment_path is None:
        experiment_path = finders.find("search/experiments")
        analysis_path = os.path.join(experiment_path, experiment, analysis.accession_id)
    else:
        analysis_path = os.path.join(experiment_path, analysis.accession_id)

    return analysis_path


def create_analysis_dir(analysis):
    os.makedirs(analysis_dir(analysis), exist_ok=True)


def delete_analysis_dir(analysis):
    shutil.rmtree(analysis_dir(analysis))


def gen_coverage(analysis: Analysis, bin_size=2_000_000, chrom_name=None):
    experiment = analysis.experiment_id
    analysis_dir = finders.find(f"search/experiments/{experiment}/{analysis.accession_id}")

    results = analysis.files.all()[0].data_file_info

    args = ["cov_viz", analysis_dir, analysis.accession_id, results.ref_genome.upper(), str(bin_size)]

    if chrom_name is not None:
        args.append(chrom_name)

    run(
        args,
        check=True,
        env={"PATH": os.getenv("PATH"), "DATABASE_URL": os.getenv("DATABASE_URL")},
    )


def gen_coverage_manifest(analysis: Analysis):
    experiment = analysis.experiment_id
    analysis_dir = finders.find(f"search/experiments/{experiment}/{analysis.accession_id}")

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


def gen_all_coverage(analysis_accession):
    analysis = Analysis.objects.get(accession_id=analysis_accession)

    create_analysis_dir(analysis)

    try:
        gen_coverage(analysis, bin_size=2_000_000)
        gen_coverage_manifest(analysis)
        for chrom_name in [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21",
            "22",
            "X",
            "Y",
            "MT",
        ]:
            gen_coverage(analysis, bin_size=100_000, chrom_name=f"chr{chrom_name}")
    except CalledProcessError as cpe:
        delete_analysis_dir(analysis)
        raise cpe
