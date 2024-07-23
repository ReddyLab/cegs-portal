# Generated by Django 4.2.11 on 2024-07-18 17:37

import cegs_portal.search.models.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0060_analysis_p_value_adj_method_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExperimentCollection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "accession_id",
                    models.CharField(
                        max_length=17,
                        unique=True,
                        validators=[cegs_portal.search.models.validators.validate_accession_id],
                    ),
                ),
                ("archived", models.BooleanField(default=False)),
                ("public", models.BooleanField(default=True)),
                ("facet_num_values", models.JSONField(blank=True, null=True)),
                ("name", models.CharField(max_length=512)),
                ("description", models.CharField(blank=True, max_length=4096, null=True)),
                ("experiments", models.ManyToManyField(blank=True, related_name="collections", to="search.experiment")),
                ("facet_values", models.ManyToManyField(blank=True, to="search.facetvalue")),
            ],
            options={
                "abstract": False,
                "indexes": [models.Index(fields=["accession_id"], name="expcol_accession_id_index")],
            },
        ),
    ]
