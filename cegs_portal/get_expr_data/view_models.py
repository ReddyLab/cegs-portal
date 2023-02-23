import csv
import os
import re
from enum import Enum
from uuid import UUID, uuid4

from django.core.files.storage import default_storage
from django.db import connection
from psycopg2.extras import NumericRange

from cegs_portal.tasks.decorators import as_task

EXPR_DATA_DIR = "expr_data_dir"


class InvalidDataSource(Exception):
    pass


class ReoDataSource(Enum):
    SOURCES = 1
    TARGETS = 2
    BOTH = 3


def validate_expr(expr) -> bool:
    return re.match(r"^DCPEXPR[A-F0-9]{8}$", expr) is not None


def gen_output_filename(experiments) -> str:
    return f"{'.'.join(experiments)}.{uuid4()}.tsv"


def validate_filename(filename: str) -> bool:
    file_sections = filename.split(".")

    try:
        UUID(file_sections[-2])
    except ValueError:
        return False

    return file_sections[-1] == "tsv" and all(validate_expr(f) for f in file_sections[0:-2])


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


def output_experiment_data(
    regions: list[tuple[str, int, int]], experiments: list[str], data_source: ReoDataSource, output_filename: str
):
    experiment_data = retrieve_experiment_data(regions, experiments, data_source)
    full_output_path = os.path.join(default_storage.location, EXPR_DATA_DIR, output_filename)

    with open(full_output_path, "w", encoding="utf-8") as output:
        csv_writer = csv.writer(output, delimiter="\t")
        csv_writer.writerow(
            [
                "Source Locs",
                "Target Info",
                "p-value",
                "Adjusted p-value",
                "Effect Size",
                "Expr Accession Id",
            ]
        )
        for source_locs, target_info, _reo_accesion_id, effect_size, p_value, sig, expr_accession_id in experiment_data:
            csv_writer.writerow(
                [
                    ",".join(parse_source_locs(source_locs)),
                    ",".join(parse_target_info(target_info)),
                    p_value,
                    effect_size,
                    sig,
                    expr_accession_id,
                ]
            )


def retrieve_experiment_data(regions: list[tuple[str, int, int]], experiments: list[str], data_source: ReoDataSource):
    if data_source == ReoDataSource.SOURCES:
        where = r"""WHERE reo_sources_targets.source_chrom = %s
                        AND reo_sources_targets.source_loc && %s
                        AND reo_sources_targets.reo_experiment = ANY(%s)"""
        inputs = [[chrom, NumericRange(start, end), experiments] for chrom, start, end in regions]
    elif data_source == ReoDataSource.TARGETS:
        where = r"""WHERE reo_sources_targets.target_chrom = %s
                        AND reo_sources_targets.target_loc && %s
                        AND reo_sources_targets.reo_experiment = ANY(%s)"""
        inputs = [[chrom, NumericRange(start, end), experiments] for chrom, start, end in regions]
    elif data_source == ReoDataSource.BOTH:
        where = r"""WHERE (reo_sources_targets.source_chrom = %s AND reo_sources_targets.source_loc && %s)
                        OR (reo_sources_targets.target_chrom = %s AND reo_sources_targets.target_loc && %s)
                        AND reo_sources_targets.reo_experiment = ANY(%s)"""
        inputs = [
            [chrom, NumericRange(start, end), chrom, NumericRange(start, end), experiments]
            for chrom, start, end in regions
        ]
    else:
        raise InvalidDataSource()

    query = f"""SELECT ARRAY_AGG(DISTINCT
                            (reo_sources_targets.source_chrom,
                             reo_sources_targets.source_loc)) AS sources,
                        ARRAY_AGG(DISTINCT
                            (reo_sources_targets.target_chrom,
                             reo_sources_targets.target_loc,
                             reo_sources_targets.target_gene_symbol,
                             reo_sources_targets.target_ensembl_id)) AS targets,
                        reo_sources_targets.reo_accession as ai,
                        reo_sources_targets.reo_facets ->> 'Effect Size' as effect_size,
                        reo_sources_targets.reo_facets ->> 'Raw p value' as raw_p_value,
                        reo_sources_targets.reo_facets ->> 'Significance' as sig,
                        reo_sources_targets.reo_experiment as eai
                    FROM reo_sources_targets
                    WHERE reo_sources_targets.reo_accession = ANY(SELECT DISTINCT reo_sources_targets.reo_accession
                                                                  FROM reo_sources_targets
                                                                  {where})
                    GROUP BY ai, reo_sources_targets.reo_facets, eai"""

    with connection.cursor() as cursor:
        experiment_data = set()

        for where_params in inputs:
            cursor.execute(query, where_params)
            experiment_data.update(cursor.fetchall())
    return experiment_data


output_experiment_data_task = as_task()(output_experiment_data)
