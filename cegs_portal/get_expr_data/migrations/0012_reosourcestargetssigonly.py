# Generated by Django 4.2 on 2023-05-22 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("get_expr_data", "0011_auto_20230516_1123"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReoSourcesTargetsSigOnly",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ],
            options={
                "db_table": "reo_sources_targets_sig_only",
                "managed": False,
            },
        ),
    ]
