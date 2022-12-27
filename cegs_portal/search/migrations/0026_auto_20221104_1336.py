# Generated by Django 4.1.3 on 2022-11-04 17:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0025_dnafeature_archived_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            """UPDATE search_regulatoryeffectobservation SET experiment_accession_id =
            (SELECT sexper.accession_id
	         FROM search_experiment as sexper
             WHERE sexper.id = search_regulatoryeffectobservation.experiment_id)""",
            reverse_sql="UPDATE search_regulatoryeffectobservation SET experiment_accession_id = null",
        ),
        migrations.RunSQL(
            """UPDATE search_dnafeature AS sdf1 SET experiment_accession_id =
            (SELECT sexper.accession_id
            FROM search_experiment as sexper
            JOIN search_experiment_other_files as seof ON sexper.id = seof.experiment_id
            JOIN search_dnafeature as sdf2 on sdf2.source_id = seof.file_id
            WHERE sdf1.id = sdf2.id)""",
            reverse_sql="UPDATE search_dnafeature SET experiment_accession_id = null",
        ),
    ]
