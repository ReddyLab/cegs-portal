# Generated by Django 4.1 on 2022-10-04 20:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0016_dnafeature_closest_gene_ensembl_id"),
    ]

    operations = [
        migrations.RunSQL(
            """
            WITH cg AS (
                SELECT sd1.id, sd2.ensembl_id
                FROM search_dnafeature as sd1
                JOIN search_dnafeature as sd2 ON sd1.closest_gene_id = sd2.id
            ) UPDATE search_dnafeature SET closest_gene_ensembl_id = cg.ensembl_id
                FROM cg WHERE search_dnafeature.id = cg.id""",
            reverse_sql="""
            UPDATE search_dnafeature SET closest_gene_ensembl_id = null
            WHERE search_dnafeature.closest_gene_id is not null""",
        ),
    ]
