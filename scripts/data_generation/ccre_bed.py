import argparse
import sys
from os import getenv

import psycopg2
from psycopg2 import sql


def get_args():
    parser = argparse.ArgumentParser(description="Get all the cCREs for particular assembly")
    parser.add_argument("-a", "--assembly", help="Genome assembly (GRCh37 or GRCh38)", required=True)
    parser.add_argument(
        "-o", "--output", help="Output file", type=argparse.FileType("w", encoding="ascii"), default=sys.stdout
    )

    return parser.parse_args()


if __name__ == "__main__":
    database_connection = getenv("DATABASE_URL")
    if database_connection is None:
        exit("Please set a DATABASE_URL environment variable")
    args = get_args()

    if args.assembly not in ["GRCh37", "GRCh38"]:
        exit("Please enter either GRCh37 or GRCh38 for the assembly")

    with psycopg2.connect(database_connection) as connection:
        with connection.cursor() as cursor:
            cursor.copy_expert(
                sql.SQL(
                    """COPY (SELECT chrom_name, lower(location), upper(location)
FROM public.search_dnafeature
WHERE feature_type = 'DNAFeatureType.CCRE' and ref_genome = {}
ORDER BY chrom_name, lower(location)) TO STDOUT WITH NULL AS ''"""
                ).format(sql.Literal(args.assembly)),
                args.output,
            )
