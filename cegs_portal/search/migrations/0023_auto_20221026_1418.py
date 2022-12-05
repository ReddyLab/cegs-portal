# Generated by Django 4.1 on 2022-10-26 18:18

from django.db import migrations, transaction
from cegs_portal.search.models import AccessionIds, AccessionType

KNOWN_TISSUE_TYPES = {
    "iPSC": "Stem",
    "k562": "Bone marrow",
    "NPC": "Stem",
    "CD8": "T cell",
}


def gen_biosamples(apps, schema_editor):
    Experiment = apps.get_model("search", "Experiment")
    Biosample = apps.get_model("search", "Biosample")
    CellLine = apps.get_model("search", "CellLine")
    TissueType = apps.get_model("search", "TissueType")
    experiments: list[Experiment] = list(Experiment.objects.prefetch_related("data_files").all())

    with AccessionIds(message="Data migration 0023") as accession_ids:
        with transaction.atomic():
            for experiment in experiments:
                for file in experiment.data_files.all():
                    tissue_type_name = KNOWN_TISSUE_TYPES[file.cell_line]
                    cell_line = CellLine.objects.filter(name=file.cell_line, tissue_type_name=tissue_type_name).first()
                    if cell_line is None:
                        tissue_type, tt_created = TissueType.objects.get_or_create(name=tissue_type_name)
                        if tt_created:
                            tissue_type.accession_id = accession_ids.incr(AccessionType.TT)
                            tissue_type.save()
                        cell_line = CellLine(
                            name=file.cell_line,
                            accession_id=accession_ids.incr(AccessionType.CL),
                            tissue_type=tissue_type,
                            tissue_type_name=tissue_type_name,
                        )
                        cell_line.save()

                    bios = Biosample(
                        cell_line=cell_line,
                        cell_line_name=cell_line.name,
                        accession_id=accession_ids.incr(AccessionType.BIOS),
                    )
                    bios.save()

                    experiment.biosamples.add(bios)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("search", "0022_rename_line_name_cellline_name_and_more"),
    ]

    operations = [migrations.RunPython(gen_biosamples)]
