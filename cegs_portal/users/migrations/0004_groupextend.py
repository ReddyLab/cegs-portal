# Generated by Django 4.1.3 on 2022-11-15 18:49

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("users", "0003_user_experiments"),
    ]

    operations = [
        migrations.CreateModel(
            name="GroupExtension",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=1024, null=True, verbose_name="Group Description")),
                (
                    "experiments",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=15, verbose_name="Associated Experiments"),
                        default=list,
                        size=None,
                    ),
                ),
                ("group", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="auth.group")),
            ],
        ),
    ]
