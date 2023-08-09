# Generated by Django 4.2 on 2023-04-21 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("get_expr_data", "0006_experimentdata_created_at"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="experimentdata",
            name="data",
        ),
        migrations.AddField(
            model_name="experimentdata",
            name="file",
            field=models.FilePathField(
                default="", path="/Users/tc325/Documents/ccgr_portal/portal/cegs_portal/media/expr_data_dir"
            ),
            preserve_default=False,
        ),
    ]
