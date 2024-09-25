# Generated by Django 5.1 on 2024-09-24 14:04

from django.db import migrations

from cegs_portal.search.models.dna_feature import DNAFeature


def update_experiment_type(apps, schema_editor):
    Experiment = apps.get_model("search", "Experiment")

    Experiment.objects.filter(experiment_type="scCERES").update(experiment_type="Perturb-Seq")
    Experiment.objects.filter(experiment_type="wgCERES").update(experiment_type="Proliferation screen")


def revert_experiment_type(apps, schema_editor):
    Experiment = apps.get_model("search", "Experiment")

    Experiment.objects.filter(experiment_type="Perturb-Seq").update(experiment_type="scCERES")
    Experiment.objects.filter(experiment_type="Proliferation screen").update(experiment_type="wgCERES")


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0063_auto_20240830_0810"),
    ]

    operations = [
        migrations.RunPython(update_experiment_type, revert_experiment_type),
    ]
