from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    Biosample,
    CellLine,
    TissueType,
)


class ExperimentBiosample:
    cell_line: str
    tissue_type: str
    description: str

    def __init__(self, bio_metadata: dict[str, str]):
        self.name = bio_metadata.get("name", None)
        self.description = bio_metadata.get("description", None)
        self.cell_line = bio_metadata["cell_type"]
        self.tissue_type = bio_metadata["tissue_type"]

    def db_save(self, experiment):
        cell_line = CellLine.objects.filter(name=self.cell_line).first()
        if cell_line is None:
            with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
                tissue_type, tt_created = TissueType.objects.get_or_create(name=self.tissue_type)
                if tt_created:
                    tissue_type.accession_id = accession_ids.incr(AccessionType.TT)
                    tissue_type.save()
                cell_line = CellLine(
                    name=self.cell_line,
                    accession_id=accession_ids.incr(AccessionType.CL),
                    tissue_type=tissue_type,
                    tissue_type_name=self.tissue_type,
                )
                cell_line.save()
        bios = Biosample.objects.filter(
            cell_line=cell_line,
            cell_line_name=cell_line.name,
        ).first()
        if bios is None:
            with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
                bios = Biosample(
                    cell_line=cell_line,
                    cell_line_name=cell_line.name,
                    accession_id=accession_ids.incr(AccessionType.BIOS),
                )
                bios.save()
        return bios
