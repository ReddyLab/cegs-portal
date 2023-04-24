import csv
import os
import re
from enum import Enum
from operator import itemgetter
from typing import Optional, TypedDict
from uuid import UUID, uuid4

from django.core.files.storage import default_storage
from django.db import connection
from psycopg2.extras import NumericRange

from cegs_portal.tasks.decorators import as_task

TargetJson = TypedDict(
    "TargetJson",
    {
        "gene sym": str,
        "gene id": str,
    },
)
ExperimentDataJson = TypedDict(
    "ExperimentDataJson",
    {
        "source locs": list[str],
        "targets": list[TargetJson],
        "p-val": float,
        "adj p-val": float,
        "effect size": Optional[float],
        "expr id": str,
        "analysis id": str,
    },
)

EXPR_DATA_DIR = "expr_data_dir"


class InvalidDataSource(Exception):
    pass


class ReoDataSource(Enum):
    SOURCES = 1
    TARGETS = 2
    BOTH = 3


def validate_expr(expr) -> bool:
    return re.match(r"^DCPEXPR[A-F0-9]{8}$", expr) is not None


def validate_an(expr) -> bool:
    return re.match(r"^DCPAN[A-F0-9]{8}$", expr) is not None


def gen_output_filename(experiments, analyses) -> str:
    search_items = experiments.copy()
    search_items.extend(analyses)
    return f"{'.'.join(search_items)}.{uuid4()}.tsv"


def validate_filename(filename: str) -> bool:
    file_sections = filename.split(".")

    try:
        UUID(file_sections[-2])
    except ValueError:
        return False

    return file_sections[-1] == "tsv" and all(validate_expr(f) or validate_an(f) for f in file_sections[0:-2])


def parse_source_locs(source_locs: str) -> list[str]:
    locs = []
    while match := re.search(r'\((chr\w+),\\"\[(\d+),(\d+)\)\\"\)', source_locs):
        chrom = match[1]
        start = match[2]
        end = match[3]
        locs.append(f"{chrom}:{start}-{end}")
        source_locs = source_locs[match.end() :]

    return locs


def parse_target_info(target_info: str) -> list[str]:
    info = []
    while match := re.search(r'\(chr\w+,\\"\[\d+,\d+\)\\",([\w-]+),(\w+)\)', target_info):
        gene_symbol = match[1]
        ensembl_id = match[2]
        info.append(f"{gene_symbol}:{ensembl_id}")
        target_info = target_info[match.end() :]
    return info


def gen_output_rows(experiment_data):
    for (
        source_locs,
        target_info,
        _reo_accesion_id,
        effect_size,
        p_value,
        sig,
        expr_accession_id,
        analysis_accession_id,
    ) in experiment_data:
        yield [
            parse_source_locs(source_locs),
            parse_target_info(target_info),
            p_value,
            sig,
            effect_size,
            expr_accession_id,
            analysis_accession_id,
        ]


def write_experiment_data_csv(experiment_data, output_file):
    csv_writer = csv.writer(output_file, delimiter="\t", lineterminator="\n")
    csv_writer.writerow(
        [
            "Source Locs",
            "Target Info",
            "p-value",
            "Adjusted p-value",
            "Effect Size",
            "Expr Accession Id",
            "Analysis Accession Id",
        ]
    )
    for row in gen_output_rows(experiment_data):
        row[0] = ",".join(row[0])
        row[1] = ",".join(row[1])
        csv_writer.writerow(row)


def output_experiment_data_list(
    regions: list[tuple[str, int, int]], experiments: list[str], analyses: list[str], data_source: ReoDataSource
) -> list[ExperimentDataJson]:
    experiment_data = retrieve_experiment_data(regions, experiments, analyses, data_source)
    exp_data_list = []
    for row in gen_output_rows(experiment_data):
        split_target_info = [target.split(":") for target in row[1]]

        # Some observations have null effect sizes
        try:
            effect_size = float(row[4])
        except TypeError:
            effect_size = None
        except ValueError:
            effect_size = None

        exp_data_list.append(
            {
                "source locs": row[0],
                "targets": [{"gene sym": gene_sym, "gene id": gene_id} for gene_sym, gene_id in split_target_info],
                "p-val": float(row[2]),
                "adj p-val": float(row[3]),
                "effect size": effect_size,
                "expr id": row[5],
                "analysis id": row[6],
            }
        )
    # Sort so the output is always in the same order. This isn't otherwise guaranteed because the
    # output of retrieve_experiment_data is a set, which is unordered.
    exp_data_list.sort(key=itemgetter("source locs", "targets"))
    return exp_data_list


def output_experiment_data_csv(
    regions: list[tuple[str, int, int]],
    experiments: list[str],
    analyses: list[str],
    data_source: ReoDataSource,
    output_filename: str,
):
    experiment_data = retrieve_experiment_data(regions, experiments, analyses, data_source)
    full_output_path = os.path.join(default_storage.location, EXPR_DATA_DIR, output_filename)
    with open(full_output_path, "w", encoding="utf-8") as output_file:
        write_experiment_data_csv(experiment_data, output_file)


def retrieve_experiment_data(
    regions: list[tuple[str, int, int]], experiments: list[str], analyses: list[str], data_source: ReoDataSource
):
    if data_source == ReoDataSource.SOURCES:
        where = r"""WHERE reo_sources_targets.source_chrom = %s
                        AND reo_sources_targets.source_loc && %s"""
        inputs = [[chrom, NumericRange(start, end)] for chrom, start, end in regions]
    elif data_source == ReoDataSource.TARGETS:
        where = r"""WHERE reo_sources_targets.target_chrom = %s
                        AND reo_sources_targets.target_loc && %s"""
        inputs = [[chrom, NumericRange(start, end)] for chrom, start, end in regions]
    elif data_source == ReoDataSource.BOTH:
        where = r"""WHERE (reo_sources_targets.source_chrom = %s AND reo_sources_targets.source_loc && %s)
                        OR (reo_sources_targets.target_chrom = %s AND reo_sources_targets.target_loc && %s)"""
        inputs = [[chrom, NumericRange(start, end), chrom, NumericRange(start, end)] for chrom, start, end in regions]
    else:
        raise InvalidDataSource()

    if len(experiments) > 0 and len(analyses) > 0:
        where = f"""{where} AND (reo_sources_targets.reo_experiment = ANY(%s) OR
        reo_sources_targets.reo_analysis = ANY(%s))"""
        for i in inputs:
            i.append(experiments)
            i.append(analyses)
    elif len(experiments) > 0:
        where = f"{where} AND reo_sources_targets.reo_experiment = ANY(%s)"
        for i in inputs:
            i.append(experiments)
    elif len(analyses) > 0:
        where = f"{where} AND reo_sources_targets.reo_analysis = ANY(%s)"
        for i in inputs:
            i.append(analyses)

    query = f"""SELECT ARRAY_AGG(DISTINCT
                            (reo_sources_targets.source_chrom,
                             reo_sources_targets.source_loc)) AS sources,
                        ARRAY_AGG(DISTINCT
                            (reo_sources_targets.target_chrom,
                             reo_sources_targets.target_loc,
                             reo_sources_targets.target_gene_symbol,
                             reo_sources_targets.target_ensembl_id)) AS targets,
                        reo_sources_targets.reo_accession as ai, -- ai = accession id
                        reo_sources_targets.reo_facets ->> 'Effect Size' as effect_size,
                        reo_sources_targets.reo_facets ->> 'Raw p value' as raw_p_value,
                        reo_sources_targets.reo_facets ->> 'Significance' as sig,
                        reo_sources_targets.reo_experiment as eai, -- eai = experiment accession id
                        reo_sources_targets.reo_analysis as aai -- aai = analysis accession id
                    FROM reo_sources_targets
                    WHERE reo_sources_targets.reo_accession = ANY(SELECT DISTINCT reo_sources_targets.reo_accession
                                                                  FROM reo_sources_targets
                                                                  {where})
                    GROUP BY ai, reo_sources_targets.reo_facets, eai, aai"""

    with connection.cursor() as cursor:
        experiment_data = set()

        for where_params in inputs:
            cursor.execute(query, where_params)
            experiment_data.update(cursor.fetchall())
    return experiment_data


output_experiment_data_csv_task = as_task()(output_experiment_data_csv)
