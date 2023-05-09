# Generated by Django 4.2 on 2023-05-04 17:29

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("get_expr_data", "0009_experimentdata_filename"),
    ]

    operations = [
        migrations.RunSQL("DROP MATERIALIZED VIEW IF EXISTS reo_sources_targets"),
        migrations.RunSQL(
            """CREATE MATERIALIZED VIEW reo_sources_targets AS
                SELECT sr.id AS reo_id,
                    sr.accession_id AS reo_accession,
                    sr.experiment_accession_id AS reo_experiment,
                    sr.analysis_accession_id AS reo_analysis,
                    sr.facet_num_values AS reo_facets,
                    sds.id AS source_id,
                    sds.accession_id AS source_accession,
                    sds.chrom_name AS source_chrom,
                    sds.location AS source_loc,
                    sdt.id AS target_id,
                    sdt.accession_id AS target_accession,
                    sdt.chrom_name AS target_chrom,
                    sdt.location AS target_loc,
                    sdt.name AS target_gene_symbol,
                    sdt.ensembl_id AS target_ensembl_id,
                    array_remove(ARRAY_AGG(DISTINCT(srfv.facetvalue_id)) || ARRAY_AGG(DISTINCT(sdsfv.facetvalue_id)) || ARRAY_AGG(DISTINCT(sdtfv.facetvalue_id)), NULL) AS disc_facets
                FROM search_regulatoryeffectobservation AS sr
                LEFT JOIN search_regulatoryeffectobservation_facet_values as srfv on sr.id = srfv.regulatoryeffectobservation_id
                LEFT JOIN search_regulatoryeffectobservation_sources AS srs ON sr.id = srs.regulatoryeffectobservation_id
                LEFT JOIN search_regulatoryeffectobservation_targets AS srt ON sr.id = srt.regulatoryeffectobservation_id
                LEFT JOIN search_dnafeature AS sds ON sds.id = srs.dnafeature_id
                LEFT JOIN search_dnafeature_facet_values as sdsfv on sds.id = sdsfv.dnafeature_id
                LEFT JOIN search_dnafeature AS sdt ON sdt.id = srt.dnafeature_id
                LEFT JOIN search_dnafeature_facet_values as sdtfv on sdt.id = sdtfv.dnafeature_id
                GROUP BY sr.id, sds.id, sdt.id
                """,
            "DROP MATERIALIZED VIEW reo_sources_targets",
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_rst_reo_accession ON reo_sources_targets (reo_accession)",
            "DROP INDEX idx_rst_reo_accession",
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_rst_reo_experiment ON reo_sources_targets (reo_experiment)",
            "DROP INDEX idx_rst_reo_experiment",
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_rst_reo_analysis ON reo_sources_targets (reo_analysis)",
            "DROP INDEX idx_rst_reo_analysis",
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_rst_source_chrom ON reo_sources_targets (source_chrom)", "DROP INDEX idx_rst_source_chrom"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_rst_source_loc ON reo_sources_targets USING GIST (source_loc)",
            "DROP INDEX idx_rst_source_loc",
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_srs_target_chrom ON reo_sources_targets (target_chrom)", "DROP INDEX idx_srs_target_chrom"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_srs_target_loc ON reo_sources_targets USING GIST (target_loc)",
            "DROP INDEX idx_srs_target_loc",
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_disc_facet ON reo_sources_targets USING GIN (disc_facets)",
            "DROP INDEX idx_disc_facet",
        ),
    ]
