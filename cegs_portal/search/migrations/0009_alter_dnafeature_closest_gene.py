# Generated by Django 4.0.3 on 2022-07-28 15:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0008_alter_regulatoryeffect_sources_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dnafeature",
            name="closest_gene",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="closest_features",
                to="search.dnafeature",
            ),
        ),
    ]
