import logging
import os
from subprocess import CalledProcessError

from django.contrib.staticfiles import finders

from cegs_portal.search.models import Analysis

from .experiment_coverage import gen_coverage, gen_coverage_manifest
from .qq_plot import gen_qq_plot
from .volcano_plot import gen_volcano_plot

logger = logging.getLogger(__name__)


def get_analysis_dir(analysis):
    experiment = analysis.experiment_id
    experiment_path = finders.find(f"search/experiments/{experiment}")
    if experiment_path is None:
        experiment_path = finders.find("search/experiments")
        analysis_path = os.path.join(experiment_path, experiment, analysis.accession_id)
    else:
        analysis_path = os.path.join(experiment_path, analysis.accession_id)

    return analysis_path


def create_analysis_dir(analysis):
    analysis_path = get_analysis_dir(analysis)
    os.makedirs(analysis_path, exist_ok=True)
    return analysis_path


def delete_coverage_files(analysis_dir):
    analysis_dir_fd = os.open(analysis_dir, os.O_RDONLY)
    for file in os.listdir(analysis_dir):
        if file.endswith((".fd", ".ecd", "coverage_manifest.json")):
            os.remove(file, dir_fd=analysis_dir_fd)
    os.close(analysis_dir_fd)


def gen_all_coverage(analysis_accession):
    analysis = Analysis.objects.get(accession_id=analysis_accession)

    analysis_dir = create_analysis_dir(analysis)

    try:
        logger.info(f"{analysis_accession}: Generating volcano plot")
        gen_volcano_plot(analysis, analysis_dir=analysis_dir)
    except:
        logger.error(f"Volcano plot generation failed: {analysis.accession_id}")
        raise

    try:
        logger.info(f"{analysis_accession}: Generating QQ plot")
        gen_qq_plot(analysis, analysis_dir=analysis_dir)
    except:
        logger.error(f"QQ plot generation failed: {analysis.accession_id}")
        raise

    try:
        logger.info(f"{analysis_accession}: Generating coverage")
        gen_coverage(analysis, analysis_dir=analysis_dir)
        gen_coverage_manifest(analysis, analysis_dir=analysis_dir)
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
            gen_coverage(analysis, analysis_dir=analysis_dir, bin_size=100_000, chrom_name=f"chr{chrom_name}")
    except:
        delete_coverage_files(analysis_dir)
        logger.error(f"Coverage generation failed: {analysis.accession_id}")
        raise
