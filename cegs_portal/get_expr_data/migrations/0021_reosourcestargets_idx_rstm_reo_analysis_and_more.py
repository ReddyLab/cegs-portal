# Generated by Django 4.2.11 on 2024-04-25 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("get_expr_data", "0020_reosourcestargetssigonlymodel_reosourcestargetsmodel"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="reosourcestargets",
            index=models.Index(fields=["reo_analysis"], name="idx_rstm_reo_analysis"),
        ),
        migrations.AddIndex(
            model_name="reosourcestargetssigonly",
            index=models.Index(fields=["reo_analysis"], name="idx_rstsom_reo_analysis"),
        ),
    ]
