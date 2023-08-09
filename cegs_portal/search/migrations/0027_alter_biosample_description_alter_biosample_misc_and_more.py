# Generated by Django 4.1.3 on 2022-11-17 21:11

import cegs_portal.search.models.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0026_auto_20221104_1336"),
    ]

    operations = [
        migrations.AlterField(
            model_name="biosample",
            name="description",
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="biosample",
            name="misc",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="biosample",
            name="name",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="cellline",
            name="description",
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="cell_line",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="closest_gene",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="closest_features",
                to="search.dnafeature",
            ),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="closest_gene_distance",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="closest_gene_ensembl_id",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="closest_gene_name",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="ensembl_id",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="experiment_accession",
            field=models.ForeignKey(
                blank=True,
                db_column="experiment_accession_id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="search.experiment",
                to_field="accession_id",
            ),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="facet_num_values",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="facet_values",
            field=models.ManyToManyField(blank=True, to="search.facetvalue"),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="feature_subtype",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="ids",
            field=models.JSONField(
                blank=True, null=True, validators=[cegs_portal.search.models.validators.validate_gene_ids]
            ),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="misc",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="name",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="children",
                to="search.dnafeature",
            ),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="ref_genome_patch",
            field=models.CharField(default="0", max_length=10),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="source",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="search.file"
            ),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="strand",
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="biosamples",
            field=models.ManyToManyField(blank=True, related_name="experiments", to="search.biosample"),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="description",
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="experiment_type",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="facet_num_values",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="facet_values",
            field=models.ManyToManyField(blank=True, to="search.facetvalue"),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="other_files",
            field=models.ManyToManyField(blank=True, related_name="experiments", to="search.file"),
        ),
        migrations.AlterField(
            model_name="experimentdatafile",
            name="description",
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="file",
            name="description",
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name="file",
            name="facet_num_values",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="file",
            name="facet_values",
            field=models.ManyToManyField(blank=True, to="search.facetvalue"),
        ),
        migrations.AlterField(
            model_name="file",
            name="url",
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AlterField(
            model_name="regulatoryeffectobservation",
            name="facet_num_values",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="regulatoryeffectobservation",
            name="facet_values",
            field=models.ManyToManyField(blank=True, to="search.facetvalue"),
        ),
        migrations.AlterField(
            model_name="regulatoryeffectobservation",
            name="sources",
            field=models.ManyToManyField(blank=True, related_name="source_for", to="search.dnafeature"),
        ),
        migrations.AlterField(
            model_name="regulatoryeffectobservation",
            name="targets",
            field=models.ManyToManyField(blank=True, related_name="target_of", to="search.dnafeature"),
        ),
        migrations.AlterField(
            model_name="tissuetype",
            name="description",
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
    ]
