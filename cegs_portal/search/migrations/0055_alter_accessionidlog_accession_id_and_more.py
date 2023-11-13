# Generated by Django 4.2.3 on 2023-10-05 18:37

import cegs_portal.search.models.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("search", "0054_alter_accessionidlog_accession_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessionidlog",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
        migrations.AlterField(
            model_name="analysis",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
        migrations.AlterField(
            model_name="biosample",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
        migrations.AlterField(
            model_name="cellline",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
        migrations.AlterField(
            model_name="dnafeature",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
        migrations.AlterField(
            model_name="experiment",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
        migrations.AlterField(
            model_name="regulatoryeffectobservation",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
        migrations.AlterField(
            model_name="tissuetype",
            name="accession_id",
            field=models.CharField(
                max_length=17, unique=True, validators=[cegs_portal.search.models.validators.validate_accession_id]
            ),
        ),
    ]
