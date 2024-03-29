# Generated by Django 4.1.6 on 2023-03-01 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0033_auto_20230227_1513"),
    ]

    operations = [
        migrations.AlterField(
            model_name="experimentdatafileinfo",
            name="p_value_threshold",
            field=models.FloatField(blank=True, default=0.05),
        ),
        migrations.AlterField(
            model_name="experimentdatafileinfo",
            name="ref_genome",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="experimentdatafileinfo",
            name="significance_measure",
            field=models.CharField(blank=True, max_length=2048),
        ),
    ]
