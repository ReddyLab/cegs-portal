# Generated by Django 5.1.4 on 2025-02-18 19:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0074_alter_accessionidlog_accession_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="regulatoryeffectobservation",
            name="name",
            field=models.CharField(blank=True, default=None, max_length=100, null=True, unique=True),
        ),
    ]
