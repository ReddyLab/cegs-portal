# Generated by Django 4.1.6 on 2023-03-28 18:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("search", "0042_auto_20230328_1404"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="analysis",
            options={"verbose_name_plural": "Analyses"},
        ),
        migrations.AddField(
            model_name="dnafeature",
            name="analysis",
            field=models.ForeignKey(
                blank=True,
                db_column="analysis_accession_id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="search.analysis",
                to_field="accession_id",
            ),
        ),
        migrations.AddField(
            model_name="regulatoryeffectobservation",
            name="analysis",
            field=models.ForeignKey(
                db_column="analysis_accession_id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="search.analysis",
                to_field="accession_id",
            ),
        ),
        migrations.AlterField(
            model_name="pipeline",
            name="analysis",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="pipelines", to="search.analysis"
            ),
        ),
    ]
