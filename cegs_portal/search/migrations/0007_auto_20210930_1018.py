# Generated by Django 3.2.6 on 2021-09-30 14:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0006_auto_20210930_1316'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GencodeGFF3Annotation',
            new_name='GencodeAnnotation',
        ),
        migrations.RenameModel(
            old_name='GencodeGFF3Region',
            new_name='GencodeRegion',
        ),
    ]
