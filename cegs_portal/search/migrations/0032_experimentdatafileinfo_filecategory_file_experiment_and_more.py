# Generated by Django 4.1.6 on 2023-02-28 19:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0031_merge_20230206_1300"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExperimentDataFileInfo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ref_genome", models.CharField(max_length=20)),
                ("ref_genome_patch", models.CharField(blank=True, max_length=10, null=True)),
                ("significance_measure", models.CharField(max_length=2048)),
                ("p_value_threshold", models.FloatField(default=0.05)),
            ],
        ),
        migrations.CreateModel(
            name="FileCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=30)),
                ("description", models.CharField(blank=True, max_length=512, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="file",
            name="experiment",
            field=models.ForeignKey(
                blank=True,
                db_column="experiment_accession_id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="files",
                to="search.experiment",
                to_field="accession_id",
            ),
        ),
        migrations.AddField(
            model_name="file",
            name="size",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="file",
            name="category",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="search.filecategory"
            ),
        ),
        migrations.AddField(
            model_name="file",
            name="data_file_info",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="file",
                to="search.experimentdatafileinfo",
            ),
        ),
    ]
