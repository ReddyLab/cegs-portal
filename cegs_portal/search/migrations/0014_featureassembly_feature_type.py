# Generated by Django 3.2.6 on 2021-10-19 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0013_dnaregion_strand'),
    ]

    operations = [
        migrations.AddField(
            model_name='featureassembly',
            name='feature_type',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ]
