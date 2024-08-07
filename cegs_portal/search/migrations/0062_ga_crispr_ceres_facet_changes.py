# Generated by Django 4.2.11 on 2024-07-11 17:11

from django.db import migrations

from cegs_portal.search.models.dna_feature import DNAFeature


def revert_new_facets(apps, schema_editor):
    Facet = apps.get_model("search", "Facet")
    FacetValue = apps.get_model("search", "FacetValue")

    crispr = Facet.objects.filter(name="CRISPR Modulation").first()

    if crispr is not None:
        crispr.delete()

    ga = Facet.objects.filter(name="Genome Assembly").first()

    if ga is not None:
        ga.delete()

    # Perturb Seq -> scCERES
    sc_value = FacetValue.objects.filter(value="Perturb-Seq").first()
    if sc_value is not None:
        sc_value.value = "scCERES"
        sc_value.save()

    # Proliferation Screen -> wgCERES
    wg_value = FacetValue.objects.filter(value="Proliferation screen").first()
    if sc_value is not None:
        wg_value.value = "wgCERES"
        wg_value.save()


def add_new_facets(apps, schema_editor):
    Facet = apps.get_model("search", "Facet")
    FacetValue = apps.get_model("search", "FacetValue")

    # scCERES -> Perturb Seq
    sc_value = FacetValue.objects.filter(value="scCERES").first()
    if sc_value is not None:
        sc_value.value = "Perturb-Seq"
        sc_value.save()

    # wgCERES -> Proliferation Screen
    wg_value = FacetValue.objects.filter(value="wgCERES").first()
    if sc_value is not None:
        wg_value.value = "Proliferation screen"
        wg_value.save()

    # +CRISPR, if it hasn't already been added
    crispr = Facet.objects.filter(name="CRISPR Modulation").first()
    if crispr is None:
        crispr = Facet(name="CRISPR Modulation", description="CRISPR modulation method", facet_type="Categorical")
        crispr.save()

        crispri = FacetValue(value="CRISPRi", facet=crispr)
        crispri.save()

        crispra = FacetValue(value="CRISPRa", facet=crispr)
        crispra.save()

    # +Genome Assembly, if it hasn't already been added
    ga = Facet.objects.filter(name="Genome Assembly").first()
    if ga is None:
        ga = Facet(name="Genome Assembly", description="The reference genome assembly", facet_type="Categorical")
        ga.save()

        hg19 = FacetValue(value="hg19", facet=ga)
        hg19.save()

        hg38 = FacetValue(value="hg38", facet=ga)
        hg38.save()


def add_assembly_facet_to_experiments(apps, schema_editor):
    Experiment = apps.get_model("search", "Experiment")
    FacetValue = apps.get_model("search", "FacetValue")

    for experiment in Experiment.objects.select_related("default_analysis").all():
        analysis = experiment.default_analysis
        if analysis is None:
            continue

        if analysis.genome_assembly in ["GRCh37", "hg19"]:
            ga = "hg19"
        elif analysis.genome_assembly in ["GRCh38", "hg38"]:
            ga = "hg38"
        else:
            continue

        ga_facet = FacetValue.objects.filter(value=ga).first()

        if ga_facet is not None:
            experiment.facet_values.add(ga_facet)
            experiment.save()


def remove_assembly_facet_from_experiments(apps, schema_editor):
    Experiment = apps.get_model("search", "Experiment")
    FacetValue = apps.get_model("search", "FacetValue")

    for experiment in Experiment.objects.select_related("default_analysis").all():
        analysis = experiment.default_analysis
        if analysis is None:
            continue

        if analysis.genome_assembly in ["GRCh37", "hg19"]:
            ga = "hg19"
        elif analysis.genome_assembly in ["GRCh38", "hg38"]:
            ga = "hg38"
        else:
            continue

        ga_facet = FacetValue.objects.filter(value=ga).first()

        if ga_facet is not None:
            experiment.facet_values.remove(ga_facet)
            experiment.save()


def update_genome_assemblies(apps, schema_editor):
    Analysis = apps.get_model("search", "Analysis")
    DNAFeature = apps.get_model("search", "DNAFeature")
    GencodeAnnotation = apps.get_model("search", "GencodeAnnotation")

    Analysis.objects.filter(genome_assembly="GRCh37").update(genome_assembly="hg19")
    Analysis.objects.filter(genome_assembly="GRCh38").update(genome_assembly="hg38")

    DNAFeature.objects.filter(ref_genome="GRCh37").update(ref_genome="hg19")
    DNAFeature.objects.filter(ref_genome="GRCh38").update(ref_genome="hg38")

    GencodeAnnotation.objects.filter(ref_genome="GRCh37").update(ref_genome="hg19")
    GencodeAnnotation.objects.filter(ref_genome="GRCh38").update(ref_genome="hg38")


def revert_genome_assemblies(apps, schema_editor):
    Analysis = apps.get_model("search", "Analysis")
    DNAFeature = apps.get_model("search", "DNAFeature")
    GencodeAnnotation = apps.get_model("search", "GencodeAnnotation")

    Analysis.objects.filter(genome_assembly="hg19").update(genome_assembly="GRCh37")
    Analysis.objects.filter(genome_assembly="hg38").update(genome_assembly="GRCh38")

    DNAFeature.objects.filter(ref_genome="hg19").update(ref_genome="GRCh37")
    DNAFeature.objects.filter(ref_genome="hg38").update(ref_genome="GRCh38")

    GencodeAnnotation.objects.filter(ref_genome="hg19").update(ref_genome="GRCh37")
    GencodeAnnotation.objects.filter(ref_genome="hg38").update(ref_genome="GRCh38")


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0061_alter_analysis_genome_assembly_and_more"),
    ]

    operations = [
        migrations.RunPython(add_new_facets, revert_new_facets),
        migrations.RunPython(add_assembly_facet_to_experiments, remove_assembly_facet_from_experiments),
        # We can automatically add the crispr facet because that information isn't
        # in the DB anywhere
        migrations.RunPython(update_genome_assemblies, revert_genome_assemblies),
    ]
