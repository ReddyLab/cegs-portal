# Generated by Django 4.1 on 2022-10-27 15:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0023_auto_20221026_1418"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="experimentdatafile",
            name="cell_line",
        ),
        migrations.RemoveField(
            model_name="experimentdatafile",
            name="cell_lines",
        ),
        migrations.RemoveField(
            model_name="experimentdatafile",
            name="tissue_types",
        ),
    ]
