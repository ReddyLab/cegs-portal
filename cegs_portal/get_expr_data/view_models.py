from enum import Enum

from django.db import connection
from psycopg2.extras import NumericRange


class InvalidDataSource(Exception):
    pass


class ReoDataSource(Enum):
    SOURCES = 1
    TARGETS = 2
    BOTH = 3


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

    query = f"""SELECT ARRAY_AGG((reo_sources_targets.source_chrom, reo_sources_targets.source_loc)) AS sources,
                        ARRAY_AGG((reo_sources_targets.target_chrom, reo_sources_targets.target_loc)) AS targets,
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
        stuff = set()

        for i in inputs:
            cursor.execute(query, i)
            stuff.update(cursor.fetchall())
    return stuff
