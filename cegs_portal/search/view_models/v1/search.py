from typing import Optional

from django.db import connection

from cegs_portal.search.models import ChromosomeLocation, Facet
from cegs_portal.search.models.utils import IdType
from cegs_portal.search.view_models.v1 import DNAFeatureSearch, LocSearchType


class Search:
    @classmethod
    def dnafeature_ids_search(cls, ids: list[tuple[IdType, str]], assembly: Optional[str]):
        return DNAFeatureSearch.ids_search(
            ids,
            assembly,
            [],
        )

    @classmethod
    def dnafeature_ids_search_public(cls, ids: list[tuple[IdType, str]], assembly: Optional[str]):
        return DNAFeatureSearch.ids_search_public(
            ids,
            assembly,
            [],
        )

    @classmethod
    def dnafeature_ids_search_with_private(
        cls, ids: list[tuple[IdType, str]], assembly: Optional[str], private_experiments: list[str]
    ):
        return DNAFeatureSearch.ids_search_with_private(
            ids,
            assembly,
            [],
            private_experiments,
        )

    @classmethod
    def dnafeature_loc_search(cls, location: ChromosomeLocation, assembly: Optional[str], facets: list[int]):
        return DNAFeatureSearch.loc_search(
            location.chromo,
            str(location.range.lower),
            str(location.range.upper),
            assembly,
            [DNAFeatureSearch.SEARCH_RESULTS_PFT],
            [],
            LocSearchType.OVERLAP.value,
            facets,
        )

    @classmethod
    def dnafeature_loc_search_public(cls, location: ChromosomeLocation, assembly: Optional[str], facets: list[int]):
        return DNAFeatureSearch.loc_search_public(
            location.chromo,
            str(location.range.lower),
            str(location.range.upper),
            assembly,
            [DNAFeatureSearch.SEARCH_RESULTS_PFT],
            [],
            LocSearchType.OVERLAP.value,
            facets,
        )

    @classmethod
    def dnafeature_loc_search_with_private(
        cls, location: ChromosomeLocation, assembly: Optional[str], facets: list[int], private_experiments: list[str]
    ):
        return DNAFeatureSearch.loc_search_with_private(
            location.chromo,
            str(location.range.lower),
            str(location.range.upper),
            assembly,
            [DNAFeatureSearch.SEARCH_RESULTS_PFT],
            [],
            LocSearchType.OVERLAP.value,
            facets,
            private_experiments,
        )

    @classmethod
    def sig_reo_loc_search(cls, location: ChromosomeLocation, private_experiments: Optional[list[str]] = None):
        private_experiments = [] if private_experiments is None else private_experiments

        where = r"""WHERE reo_sources_targets_sig_only.archived = false AND
                          (reo_sources_targets_sig_only.public = true OR
                           reo_sources_targets_sig_only.reo_experiment = ANY(%s)) AND
                          ((reo_sources_targets_sig_only.source_chrom = %s AND
                            reo_sources_targets_sig_only.source_loc && %s) OR
                           (reo_sources_targets_sig_only.target_chrom = %s AND
                            reo_sources_targets_sig_only.target_loc && %s))"""
        inputs = [private_experiments, location.chromo, location.range, location.chromo, location.range]

        query = f"""SELECT ARRAY_AGG(DISTINCT
                                (reo_sources_targets_sig_only.source_chrom,
                                reo_sources_targets_sig_only.source_loc)) AS sources,
                            ARRAY_AGG(DISTINCT
                                (reo_sources_targets_sig_only.target_chrom,
                                reo_sources_targets_sig_only.target_loc,
                                reo_sources_targets_sig_only.target_gene_symbol,
                                reo_sources_targets_sig_only.target_ensembl_id)) AS targets,
                            reo_sources_targets_sig_only.reo_accession as ai, -- ai = accession id
                            reo_sources_targets_sig_only.reo_facets ->> 'Effect Size' as effect_size,
                            reo_sources_targets_sig_only.reo_facets ->> 'Raw p value' as raw_p_value,
                            reo_sources_targets_sig_only.reo_facets ->> 'Significance' as sig,
                            reo_sources_targets_sig_only.reo_experiment as eai, -- eai = experiment accession id
                            se.name as expr_name,
                            reo_sources_targets_sig_only.reo_analysis as aai -- aai = analysis accession id
                        FROM reo_sources_targets_sig_only
                        JOIN search_experiment as se on reo_sources_targets_sig_only.reo_experiment = se.accession_id
                        WHERE reo_sources_targets_sig_only.reo_accession = ANY(
                            WITH s AS (
                                SELECT *, ROW_NUMBER()
                                OVER (PARTITION BY aai ORDER BY pval ASC)
                                FROM(SELECT reo_sources_targets_sig_only.reo_accession,
                                            reo_sources_targets_sig_only.reo_experiment as eai,
                                            reo_sources_targets_sig_only.reo_analysis as aai,
                                            (reo_sources_targets_sig_only.reo_facets->>'Raw p value')::numeric as pval
                                        FROM reo_sources_targets_sig_only
                                        {where}
                                    ) as s2)
                            SELECT reo_accession
                                FROM s
                                WHERE ROW_NUMBER <= 5
                        )
                        GROUP BY ai, reo_sources_targets_sig_only.reo_facets, eai, se.name, aai
                        ORDER BY eai, aai, raw_p_value
                        """

        with connection.cursor() as cursor:
            cursor.execute(query, inputs)
            print(cursor.query)
            experiment_data = cursor.fetchall()

        return [
            {
                "source_locs": source_locs,
                "target_info": target_info,
                "reo_accesion_id": reo_accesion_id,
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
                reo_accesion_id,
                effect_size,
                p_value,
                sig,
                expr_accession_id,
                expr_name,
                analysis_accession_id,
            ) in experiment_data
        ]

    @classmethod
    def discrete_facet_search(cls):
        return Facet.objects.filter(facet_type="FacetType.DISCRETE").prefetch_related("values").all()
