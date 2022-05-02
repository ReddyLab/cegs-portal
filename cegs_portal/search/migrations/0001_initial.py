# Generated by Django 4.0.3 on 2022-04-29 14:56

import cegs_portal.search.models.experiment
import cegs_portal.search.models.facets
import cegs_portal.search.models.validators
import django.contrib.postgres.fields
import django.contrib.postgres.fields.ranges
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CellLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='DNARegion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facet_num_values', models.JSONField(null=True)),
                ('searchable', models.BooleanField(default=True)),
                ('cell_line', models.CharField(max_length=50, null=True)),
                ('chrom_name', models.CharField(max_length=10)),
                ('closest_gene_distance', models.IntegerField()),
                ('closest_gene_name', models.CharField(max_length=50)),
                ('location', django.contrib.postgres.fields.ranges.IntegerRangeField()),
                ('misc', models.JSONField(null=True)),
                ('ref_genome', models.CharField(max_length=20)),
                ('ref_genome_patch', models.CharField(max_length=10, null=True)),
                ('region_type', models.CharField(default='', max_length=50)),
                ('strand', models.CharField(max_length=1, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facet_num_values', models.JSONField(null=True)),
                ('archived', models.BooleanField(default=False)),
                ('description', models.CharField(max_length=4096, null=True)),
                ('experiment_type', models.CharField(max_length=100, null=True)),
                ('name', models.CharField(max_length=512)),
                ('accession_id', models.CharField(max_length=8, null=True, unique=True, validators=[cegs_portal.search.models.experiment.validate_accession_id])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Facet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facet_type', models.CharField(choices=[(cegs_portal.search.models.facets.FacetType['DISCRETE'], 'Discrete'), (cegs_portal.search.models.facets.FacetType['CONTINUOUS'], 'Continuous')], default=cegs_portal.search.models.facets.FacetType['CONTINUOUS'], max_length=30)),
                ('description', models.CharField(max_length=4096, null=True)),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='FacetValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=30, null=True)),
                ('facet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='search.facet')),
            ],
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('searchable', models.BooleanField(default=True)),
                ('ensembl_id', models.CharField(default='No ID', max_length=50, unique=True)),
                ('feature_type', models.CharField(max_length=50)),
                ('feature_subtype', models.CharField(max_length=50, null=True)),
                ('misc', models.JSONField(null=True)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='search.feature')),
            ],
        ),
        migrations.CreateModel(
            name='FeatureAssembly',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('searchable', models.BooleanField(default=True)),
                ('chrom_name', models.CharField(max_length=10)),
                ('ensembl_id', models.CharField(default='No ID', max_length=50)),
                ('ids', models.JSONField(null=True, validators=[cegs_portal.search.models.validators.validate_gene_ids])),
                ('location', django.contrib.postgres.fields.ranges.IntegerRangeField()),
                ('name', models.CharField(max_length=50)),
                ('strand', models.CharField(max_length=1, null=True)),
                ('ref_genome', models.CharField(max_length=20)),
                ('ref_genome_patch', models.CharField(max_length=10)),
                ('feature_type', models.CharField(max_length=50)),
                ('feature_subtype', models.CharField(max_length=50, null=True)),
                ('misc', models.JSONField(null=True)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='search.featureassembly')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GencodeRegion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chrom_name', models.CharField(max_length=10)),
                ('base_range', django.contrib.postgres.fields.ranges.IntegerRangeField()),
            ],
        ),
        migrations.CreateModel(
            name='TissueType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tissue_type', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chromosome_name', models.CharField(max_length=10)),
                ('assembly', models.CharField(max_length=20)),
                ('location', django.contrib.postgres.fields.ranges.IntegerRangeField()),
                ('variant_id', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), size=None)),
                ('reference_base', models.CharField(max_length=100)),
                ('alternative_bases', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), null=True, size=None)),
                ('kind', models.CharField(choices=[('SNP', 'depleted'), ('enriched', 'enriched'), ('both', 'both'), ('non_sig', 'non_sig')], default='SNP', max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='VariantLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assembly', models.CharField(max_length=20)),
                ('chromosome_name', models.CharField(max_length=10)),
                ('location', django.contrib.postgres.fields.ranges.IntegerRangeField()),
            ],
        ),
        migrations.CreateModel(
            name='VCFFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('header', models.JSONField(default=dict)),
                ('sample_names', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None)),
                ('deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='VCFEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quality', models.FloatField(null=True)),
                ('filters', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, null=True, size=None)),
                ('info', models.CharField(max_length=50, null=True)),
                ('sample_format', models.CharField(max_length=50, null=True)),
                ('sample_data', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), default=list, null=True, size=None)),
                ('genotypes', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=10), default=list, null=True, size=None)),
                ('heterozygosities', django.contrib.postgres.fields.ArrayField(base_field=models.BooleanField(default=True), default=list, null=True, size=None)),
                ('phased', django.contrib.postgres.fields.ArrayField(base_field=models.BooleanField(default=True), default=list, null=True, size=None)),
                ('allele_frequency', models.FloatField()),
                ('read_depth', models.IntegerField()),
                ('mappability', models.FloatField()),
                ('deleted', models.BooleanField(default=False)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='search.vcffile')),
                ('variant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entries', to='search.variant')),
            ],
        ),
        migrations.AddField(
            model_name='variant',
            name='all_locations',
            field=models.ManyToManyField(to='search.variantlocation'),
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('subject_id', models.CharField(max_length=512, primary_key=True, serialize=False)),
                ('source', models.CharField(max_length=512)),
                ('files', models.ManyToManyField(to='search.vcffile')),
            ],
        ),
        migrations.CreateModel(
            name='RegulatoryEffect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facet_num_values', models.JSONField(null=True)),
                ('searchable', models.BooleanField(default=True)),
                ('experiment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='search.experiment')),
                ('facet_values', models.ManyToManyField(to='search.facetvalue')),
                ('sources', models.ManyToManyField(related_name='regulatory_effects', to='search.dnaregion')),
                ('target_assemblies', models.ManyToManyField(related_name='regulatory_effects', to='search.featureassembly')),
                ('targets', models.ManyToManyField(related_name='regulatory_effects', to='search.feature')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GencodeAnnotation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chrom_name', models.CharField(max_length=10)),
                ('location', django.contrib.postgres.fields.ranges.IntegerRangeField()),
                ('strand', models.CharField(max_length=1)),
                ('score', models.FloatField(null=True)),
                ('phase', models.IntegerField(null=True)),
                ('annotation_type', models.CharField(max_length=100)),
                ('id_attr', models.CharField(max_length=50)),
                ('ref_genome', models.CharField(max_length=20)),
                ('ref_genome_patch', models.CharField(max_length=10)),
                ('gene_name', models.CharField(max_length=50)),
                ('gene_type', models.CharField(max_length=50)),
                ('level', models.IntegerField()),
                ('attributes', models.JSONField(null=True)),
                ('version', models.IntegerField()),
                ('feature', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotation', to='search.feature')),
                ('feature_assembly', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotation', to='search.featureassembly')),
                ('region', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='search.gencoderegion')),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facet_num_values', models.JSONField(null=True)),
                ('filename', models.CharField(max_length=512)),
                ('description', models.CharField(max_length=4096, null=True)),
                ('url', models.CharField(max_length=2048, null=True)),
                ('facet_values', models.ManyToManyField(to='search.facetvalue')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExperimentDataFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cell_line', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=4096, null=True)),
                ('filename', models.CharField(max_length=512)),
                ('ref_genome', models.CharField(max_length=20)),
                ('ref_genome_patch', models.CharField(max_length=10)),
                ('significance_measure', models.CharField(max_length=2048)),
                ('cell_lines', models.ManyToManyField(related_name='experiment_data', to='search.cellline')),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_files', to='search.experiment')),
                ('tissue_types', models.ManyToManyField(related_name='experiment_data', to='search.tissuetype')),
            ],
        ),
        migrations.AddField(
            model_name='experiment',
            name='facet_values',
            field=models.ManyToManyField(to='search.facetvalue'),
        ),
        migrations.AddField(
            model_name='experiment',
            name='other_files',
            field=models.ManyToManyField(related_name='experiments', to='search.file'),
        ),
        migrations.AddField(
            model_name='dnaregion',
            name='closest_gene',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='search.feature'),
        ),
        migrations.AddField(
            model_name='dnaregion',
            name='closest_gene_assembly',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='search.featureassembly'),
        ),
        migrations.AddField(
            model_name='dnaregion',
            name='facet_values',
            field=models.ManyToManyField(to='search.facetvalue'),
        ),
        migrations.AddField(
            model_name='dnaregion',
            name='source',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='search.file'),
        ),
        migrations.AddIndex(
            model_name='variant',
            index=django.contrib.postgres.indexes.GistIndex(fields=['location'], name='search_variant_location_index'),
        ),
        migrations.AddIndex(
            model_name='regulatoryeffect',
            index=models.Index(fields=['searchable'], name='regulatoryeffect_srchbl_idx'),
        ),
        migrations.AddIndex(
            model_name='gencodeannotation',
            index=models.Index(fields=['annotation_type'], name='search_gen_anno_type_index'),
        ),
        migrations.AddIndex(
            model_name='featureassembly',
            index=models.Index(fields=['searchable'], name='featureassembly_srchbl_idx'),
        ),
        migrations.AddIndex(
            model_name='featureassembly',
            index=models.Index(fields=['name'], name='sfa_name_index'),
        ),
        migrations.AddIndex(
            model_name='featureassembly',
            index=models.Index(fields=['chrom_name'], name='sfa_chrom_name_index'),
        ),
        migrations.AddIndex(
            model_name='featureassembly',
            index=models.Index(fields=['feature_type'], name='sfa_feature_type_index'),
        ),
        migrations.AddIndex(
            model_name='featureassembly',
            index=django.contrib.postgres.indexes.GistIndex(fields=['location'], name='sfa_loc_index'),
        ),
        migrations.AddIndex(
            model_name='featureassembly',
            index=models.Index(fields=['ensembl_id'], name='sfa_ensembl_id_index'),
        ),
        migrations.AddIndex(
            model_name='feature',
            index=models.Index(fields=['ensembl_id'], name='sf_ensembl_id_index'),
        ),
        migrations.AddIndex(
            model_name='feature',
            index=models.Index(fields=['feature_type'], name='sf_feature_type_index'),
        ),
        migrations.AddIndex(
            model_name='facetvalue',
            index=models.Index(fields=['value'], name='sfv_value_index'),
        ),
        migrations.AddIndex(
            model_name='dnaregion',
            index=models.Index(fields=['searchable'], name='dnaregion_srchbl_idx'),
        ),
        migrations.AddIndex(
            model_name='dnaregion',
            index=django.contrib.postgres.indexes.GistIndex(fields=['location'], name='search_region_location_index'),
        ),
    ]
