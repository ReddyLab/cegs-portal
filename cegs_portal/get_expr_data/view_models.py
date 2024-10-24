import csv
import os
import re
from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto
from itertools import groupby
from operator import itemgetter
from typing import Optional, TypedDict
from uuid import UUID, uuid4

from django.core.files.storage import default_storage
from django.db import connection
from huey.contrib.djhuey import db_task
from psycopg.types.range import Int4Range, NumericRange

from cegs_portal.get_expr_data.models import ExperimentData, expr_data_base_path

MAX_FILENAME_LENGTH = 255  # This comes from the ExperimentData.filename field/maximum macos filename length

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


class InvalidDataSource(Exception):
    pass


class ReoDataSource(Enum):
    SOURCES = 1
    TARGETS = 2
    BOTH = 3
    EVERYTHING = 4


class DataState(StrEnum):
    IN_PREPARATION = auto()
    READY = auto()
    DELETED = auto()
    UNKNOWN = auto()
    NOT_FOUND = auto()


@dataclass
class Facets:
    categorical_facets: list[int] = field(default_factory=list)
    effect_size_range: Optional[tuple[float, float]] = None
    sig_range: Optional[tuple[float, float]] = None


def validate_expr(expr) -> bool:
    return re.match(r"^DCPEXPR[A-F0-9]{8,10}$", expr) is not None


def validate_an(expr) -> bool:
    return re.match(r"^DCPAN[A-F0-9]{8,10}$", expr) is not None


def gen_output_filename(experiments, analyses) -> str:
    search_items = experiments.copy() if experiments is not None else []
    search_items.extend(analyses if analyses is not None else [])
    filename_end = f".{uuid4()}.tsv"
    experiment_names = ".".join(search_items)

    max_experiment_name_length = MAX_FILENAME_LENGTH - len(filename_end)

    if len(experiment_names) > max_experiment_name_length:
        # Truncate experiment names
        experiment_names = experiment_names[:max_experiment_name_length]

    return f"{experiment_names}{filename_end}"


def validate_filename(filename: str) -> bool:
    file_sections = filename.split(".")

    try:
        UUID(file_sections[-2])
    except ValueError:
        return False

    return file_sections[-1] == "tsv" and all(validate_expr(f) or validate_an(f) for f in file_sections[0:-2])


def file_exists(filename):
    return default_storage.exists(os.path.join(expr_data_base_path(), filename))


def open_file(filename):
    return default_storage.open(os.path.join(expr_data_base_path(), filename), "rb")


def file_status(filename, user):
    try:
        data_status = ExperimentData.objects.get(filename=filename, user=user)
    except ExperimentData.DoesNotExist:
        return DataState.NOT_FOUND

    match data_status.state:
        case ExperimentData.DataState.IN_PREPARATION:
            return DataState.IN_PREPARATION
        case ExperimentData.DataState.READY:
            return DataState.READY
        case ExperimentData.DataState.DELETED:
            return DataState.DELETED
        case _:
            return DataState.UNKNOWN


def parse_source_locs(source_locs: list[tuple[Optional[str], Optional[str]]]) -> list[str]:
    locs = []
    for source_loc in source_locs:
        if source_loc[0] is None:
            continue

        chrom, loc = source_loc
        if match := re.match(r"\[(\d+),(\d+)\)", loc):
            start = match[1]
            end = match[2]
            locs.append(f"{chrom}:{start}-{end}")

    return locs


def parse_target_info(
    target_infos: list[tuple[Optional[str], Optional[str], Optional[str], Optional[str]]]
) -> list[str]:
    info = []
    for target_info in target_infos:
        if target_info[2] is None:
            continue

        _, _, gene_symbol, ensembl_id = target_info
        info.append(f"{gene_symbol}:{ensembl_id}")
    return info


def gen_output_rows(experiment_data):
    for (
        source_locs,
        target_info,
        _reo_accession_id,
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
    user_experiments,
    regions: Optional[list[tuple[str, int, int]]],
    experiments: Optional[list[str]],
    analyses: Optional[list[str]],
    data_source: ReoDataSource,
    assembly: Optional[str] = None,
) -> list[ExperimentDataJson]:
    experiment_data = retrieve_experiment_data(
        user_experiments, regions, experiments, analyses, Facets(), data_source, assembly
    )
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
    exp_data_list.sort(key=itemgetter("source locs", "expr id", "analysis id"))
    return exp_data_list


def output_experiment_data_csv(
    user,
    regions: list[tuple[str, int, int]],
    experiments: Optional[list[str]],
    analyses: Optional[list[str]],
    data_source: ReoDataSource,
    facets: Facets,
    output_filename: str,
):
    experiment_data_info = ExperimentData(user=user, filename=output_filename)
    experiment_data_info.save()
    experiment_data = retrieve_experiment_data(
        user.all_experiments(), regions, experiments, analyses, facets, data_source
    )
    full_output_path = os.path.join(expr_data_base_path(), output_filename)
    with open(full_output_path, "w", encoding="utf-8") as output_file:
        write_experiment_data_csv(experiment_data, output_file)
        experiment_data_info.file = output_file
        experiment_data_info.state = ExperimentData.DataState.READY
        experiment_data_info.save()


def retrieve_experiment_data(
    user_experiments,
    regions: Optional[list[tuple[str, int, int]]],
    experiments: Optional[list[str]],
    analyses: Optional[list[str]],
    facets: Facets,
    data_source: ReoDataSource,
    assembly: Optional[str] = None,
):
    where = r"""WHERE (get_expr_data_reo_sources_targets.archived = false AND (get_expr_data_reo_sources_targets.public = true OR
    get_expr_data_reo_sources_targets.reo_experiment = ANY(%s)))"""
    match data_source:
        case ReoDataSource.EVERYTHING:
            inputs = [[user_experiments]]
        case ReoDataSource.SOURCES | ReoDataSource.TARGETS | ReoDataSource.BOTH:
            inputs = [[user_experiments] for _ in regions]
        case _:
            raise InvalidDataSource()

    match data_source:
        case ReoDataSource.SOURCES:
            where = f"""{where} AND (get_expr_data_reo_sources_targets.source_chrom = %s
                            AND get_expr_data_reo_sources_targets.source_loc && %s)"""
            for i, (chrom, start, end) in zip(inputs, regions):
                i.append(chrom)
                i.append(Int4Range(start, end))
        case ReoDataSource.TARGETS:
            where = f"""{where} AND (get_expr_data_reo_sources_targets.target_chrom = %s
                            AND get_expr_data_reo_sources_targets.target_loc && %s)"""
            for i, (chrom, start, end) in zip(inputs, regions):
                i.append(chrom)
                i.append(Int4Range(start, end))
        case ReoDataSource.BOTH:
            where = f"""{where} AND ((get_expr_data_reo_sources_targets.source_chrom = %s AND get_expr_data_reo_sources_targets.source_loc && %s)
                            OR (get_expr_data_reo_sources_targets.target_chrom = %s AND get_expr_data_reo_sources_targets.target_loc && %s))"""
            for i, (chrom, start, end) in zip(inputs, regions):
                i.append(chrom)
                i.append(Int4Range(start, end))
                i.append(chrom)
                i.append(Int4Range(start, end))
        case ReoDataSource.EVERYTHING:
            pass
        case _:
            raise InvalidDataSource()

    if experiments is not None and analyses is not None:
        where = f"""{where} AND (get_expr_data_reo_sources_targets.reo_experiment = ANY(%s) OR
        get_expr_data_reo_sources_targets.reo_analysis = ANY(%s))"""
        for i in inputs:
            i.append(experiments)
            i.append(analyses)
    elif experiments is not None:
        where = f"{where} AND get_expr_data_reo_sources_targets.reo_experiment = ANY(%s)"
        for i in inputs:
            i.append(experiments)
    elif analyses is not None:
        where = f"{where} AND get_expr_data_reo_sources_targets.reo_analysis = ANY(%s)"
        for i in inputs:
            i.append(analyses)

    if len(facets.categorical_facets) > 0:
        where = f"{where} AND %s::bigint[] && get_expr_data_reo_sources_targets.cat_facets"
        for i in inputs:
            i.append(facets.categorical_facets)
    if facets.effect_size_range is not None:
        where = f"{where} AND %s::numrange @> (get_expr_data_reo_sources_targets.reo_facets ->> 'Effect Size')::numeric"
        for i in inputs:
            i.append(NumericRange(*facets.effect_size_range))
    if facets.sig_range is not None:
        where = f"{where} AND %s::numrange @> (get_expr_data_reo_sources_targets.reo_facets ->> '-log10 Significance')::numeric"
        for i in inputs:
            i.append(NumericRange(*facets.sig_range))

    if assembly is not None:
        where = f"{where} AND genome_assembly = %s"
        for i in inputs:
            i.append(assembly)

    query = f"""SELECT ARRAY_AGG(DISTINCT
                            (get_expr_data_reo_sources_targets.source_chrom,
                             get_expr_data_reo_sources_targets.source_loc)) AS sources,
                        ARRAY_AGG(DISTINCT
                            (get_expr_data_reo_sources_targets.target_chrom,
                             get_expr_data_reo_sources_targets.target_loc,
                             get_expr_data_reo_sources_targets.target_gene_symbol,
                             get_expr_data_reo_sources_targets.target_ensembl_id)) AS targets,
                        get_expr_data_reo_sources_targets.reo_accession as ai, -- ai = accession id
                        get_expr_data_reo_sources_targets.reo_facets ->> 'Effect Size' as effect_size,
                        get_expr_data_reo_sources_targets.reo_facets ->> 'Raw p value' as raw_p_value,
                        get_expr_data_reo_sources_targets.reo_facets ->> 'Significance' as sig,
                        get_expr_data_reo_sources_targets.reo_experiment as eai, -- eai = experiment accession id
                        get_expr_data_reo_sources_targets.reo_analysis as aai -- aai = analysis accession id
                    FROM get_expr_data_reo_sources_targets
                    WHERE get_expr_data_reo_sources_targets.reo_accession = ANY(SELECT DISTINCT get_expr_data_reo_sources_targets.reo_accession
                                                                  FROM get_expr_data_reo_sources_targets
                                                                  {where})
                    GROUP BY ai, get_expr_data_reo_sources_targets.reo_facets, eai, aai"""

    with connection.cursor() as cursor:
        experiment_data = []
        for where_params in inputs:
            cursor.execute(query, where_params)
            experiment_data.extend(cursor.fetchall())
        experiment_data.sort()
    return list(map(itemgetter(0), groupby(experiment_data)))


def sig_reo_loc_search(
    location: tuple[str, int, int],
    assembly: Optional[str] = None,
    experiments: Optional[list[str]] = None,
    count: int = 5,
    experiments_only: bool = False,
):
    experiments = [] if experiments is None else experiments

    where = r"WHERE get_expr_data_reo_sources_targets_sig_only.archived = false AND"

    if experiments_only:
        where = f"{where} (get_expr_data_reo_sources_targets_sig_only.public = true AND"
    else:
        where = f"{where} (get_expr_data_reo_sources_targets_sig_only.public = true OR"

    where = f"""{where}
                    get_expr_data_reo_sources_targets_sig_only.reo_experiment = ANY(%s)) AND
                    ((get_expr_data_reo_sources_targets_sig_only.source_chrom = %s AND
                    get_expr_data_reo_sources_targets_sig_only.source_loc && %s) OR
                    (get_expr_data_reo_sources_targets_sig_only.target_chrom = %s AND
                    get_expr_data_reo_sources_targets_sig_only.target_loc && %s))"""
    inputs = [
        experiments,
        location[0],
        Int4Range(location[1], location[2]),
        location[0],
        Int4Range(location[1], location[2]),
    ]

    if assembly is not None:
        where = f"{where} AND genome_assembly = %s"
        inputs.append(assembly)

    inputs.append(count)

    query = f"""SELECT ARRAY_AGG(DISTINCT
                            (get_expr_data_reo_sources_targets_sig_only.source_chrom,
                            get_expr_data_reo_sources_targets_sig_only.source_loc,
                            get_expr_data_reo_sources_targets_sig_only.source_accession)) AS sources,
                        ARRAY_AGG(DISTINCT
                            (get_expr_data_reo_sources_targets_sig_only.target_chrom,
                            get_expr_data_reo_sources_targets_sig_only.target_loc,
                            get_expr_data_reo_sources_targets_sig_only.target_gene_symbol,
                            get_expr_data_reo_sources_targets_sig_only.target_ensembl_id)) AS targets,
                        get_expr_data_reo_sources_targets_sig_only.reo_accession as ai, -- ai = accession id
                        get_expr_data_reo_sources_targets_sig_only.reo_facets ->> 'Effect Size' as effect_size,
                        get_expr_data_reo_sources_targets_sig_only.reo_facets ->> 'Raw p value' as raw_p_value,
                        get_expr_data_reo_sources_targets_sig_only.reo_facets ->> 'Significance' as sig,
                        get_expr_data_reo_sources_targets_sig_only.reo_experiment as eai, -- eai = experiment accession id
                        se.name as expr_name,
                        get_expr_data_reo_sources_targets_sig_only.reo_analysis as aai -- aai = analysis accession id
                    FROM get_expr_data_reo_sources_targets_sig_only
                    JOIN search_experiment as se on get_expr_data_reo_sources_targets_sig_only.reo_experiment = se.accession_id
                    WHERE get_expr_data_reo_sources_targets_sig_only.reo_accession = ANY(
                        WITH s AS (
                            SELECT *, ROW_NUMBER()
                            OVER (PARTITION BY aai ORDER BY pval ASC)
                            FROM(SELECT get_expr_data_reo_sources_targets_sig_only.reo_accession,
                                        get_expr_data_reo_sources_targets_sig_only.reo_experiment as eai,
                                        get_expr_data_reo_sources_targets_sig_only.reo_analysis as aai,
                                        (get_expr_data_reo_sources_targets_sig_only.reo_facets->>'Raw p value')::numeric as pval
                                    FROM get_expr_data_reo_sources_targets_sig_only
                                    {where}
                                ) as s2)
                        SELECT reo_accession
                            FROM s
                            WHERE ROW_NUMBER <= %s
                    )
                    GROUP BY ai, get_expr_data_reo_sources_targets_sig_only.reo_facets, eai, se.name, aai
                    ORDER BY eai, aai, raw_p_value
                    """

    with connection.cursor() as cursor:
        cursor.execute(query, inputs)
        experiment_data = cursor.fetchall()

    result = [
        {
            "source_locs": source_locs,
            "target_info": target_info if target_info != '{"(,,,)"}' else None,
            "reo_accession_id": reo_accession_id,
            "effect_size": float(effect_size) if effect_size is not None else None,
            "p_value": float(p_value) if p_value is not None else None,
            "sig": float(sig) if sig is not None else None,
            "expr_accession_id": expr_accession_id,
            "expr_name": expr_name,
            "analysis_accession_id": analysis_accession_id,
        }
        for (
            source_locs,
            target_info,
            reo_accession_id,
            effect_size,
            p_value,
            sig,
            expr_accession_id,
            expr_name,
            analysis_accession_id,
        ) in experiment_data
    ]

    return [
        (k, list(reo_group))
        for k, reo_group in groupby(result, lambda x: (x["expr_accession_id"], x["analysis_accession_id"]))
    ]


def for_facet_query_input(facets: list[int]) -> list[list[int]]:
    query_input = [facets]
    query = r"""SELECT DISTINCT facet_id FROM search_facetvalue WHERE id = ANY(%s)"""

    with connection.cursor() as cursor:
        cursor.execute(query, [facets])
        query_input.append([int(fid) for fid, in cursor.fetchall()])

    return query_input


def public_experiments_for_facets(query_input: list[list[int]]) -> set[str]:
    query = r"""SELECT accession_id
                    FROM (SELECT accession_id, bool_and(facet_table.facet_bool) as facet_match
                            FROM (SELECT se.accession_id, sefv.facetvalue_id = ANY(%s) as facet_bool
                                FROM search_experiment AS se
                                JOIN search_experiment_facet_values AS sefv ON se.id = sefv.experiment_id
                                JOIN search_facetvalue AS sfv on sfv.id = sefv.facetvalue_id
                                WHERE sfv.facet_id = ANY(%s) and se.public = true and se.archived = false
                                GROUP BY se.accession_id, sefv.facetvalue_id
                                ORDER BY se.accession_id) AS facet_table
                            GROUP BY facet_table.accession_id) AS facet_bool_table
                    WHERE facet_bool_table.facet_match = true
            """
    with connection.cursor() as cursor:
        cursor.execute(query, query_input)
        experiments = [eid for eid, in cursor.fetchall()]

    return experiments


def experiments_for_facets(query_input: list[list[int]]) -> set[str]:
    query = r"""SELECT accession_id
                    FROM (SELECT accession_id, bool_and(facet_table.facet_bool) as facet_match
                            FROM (SELECT se.accession_id, sefv.facetvalue_id = ANY(%s) as facet_bool
                                FROM search_experiment AS se
                                JOIN search_experiment_facet_values AS sefv ON se.id = sefv.experiment_id
                                JOIN search_facetvalue AS sfv on sfv.id = sefv.facetvalue_id
                                WHERE sfv.facet_id = ANY(%s)
                                GROUP BY se.accession_id, sefv.facetvalue_id
                                ORDER BY se.accession_id) AS facet_table
                            GROUP BY facet_table.accession_id) AS facet_bool_table
                    WHERE facet_bool_table.facet_match = true
            """
    with connection.cursor() as cursor:
        cursor.execute(query, query_input)
        experiments = [eid for eid, in cursor.fetchall()]

    return experiments


def analyses_for_facets(query_input: list[list[int]]) -> set[str]:
    query = r"""SELECT accession_id
                    FROM (SELECT accession_id, bool_and(facet_table.facet_bool) as facet_match
                            FROM (SELECT sa.accession_id, safv.facetvalue_id = ANY(%s) as facet_bool
                                FROM search_analysis AS sa
                                JOIN search_analysis_facet_values AS safv ON sa.id = safv.analysis_id
                                JOIN search_facetvalue AS sfv on sfv.id = safv.facetvalue_id
                                WHERE sfv.facet_id = ANY(%s)
                                GROUP BY sa.accession_id, safv.facetvalue_id
                                ORDER BY sa.accession_id) AS facet_table
                            GROUP BY facet_table.accession_id) AS facet_bool_table
                    WHERE facet_bool_table.facet_match = true
            """
    with connection.cursor() as cursor:
        cursor.execute(query, query_input)
        analyses = [aid for aid, in cursor.fetchall()]

    return analyses


output_experiment_data_csv_task = db_task()(output_experiment_data_csv)
