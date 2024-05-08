import json
import os
from typing import IO, Any, Dict, Optional

from cegs_portal.search.models import File

from .biosample import ExperimentBiosample


class FileMetadata:
    description: Optional[str]
    filename: str
    genome_assembly: str
    url: Optional[str]
    misc: dict[str, Any]
    id_: Optional[int] = None
    biosample: Optional[ExperimentBiosample] = None

    def __init__(
        self, file_metadata: Dict[str, str], base_path: str, biosamples: Optional[list[ExperimentBiosample]] = None
    ):
        self.description = file_metadata.get("description")
        self.filename = os.path.join(base_path, file_metadata["file"])
        self.genome_assembly = file_metadata["genome_assembly"]
        self.url = file_metadata.get("url")
        self.misc = file_metadata.get("misc")

        biosample_index = file_metadata.get("biosample")
        if biosample_index is not None and biosamples is not None:
            self.biosample = biosamples[biosample_index]

    def db_save(self, experiment=None, analysis=None):
        source_file = File(
            description=self.description,
            experiment=experiment,
            analysis=analysis,
            filename=os.path.basename(self.filename),
            misc=self.misc,
            url=self.url,
        )
        source_file.save()
        self.id_ = source_file.id

        return source_file

    def db_del(self):
        self.file.delete()

    def delimiter(self):
        _, ext = os.path.splitext(self.filename)
        if ext in [".csv"]:
            return ","
        elif ext in [".tsv", ".bed"]:
            return "\t"

        return ","

    @property
    def file(self):
        return File.objects.get(filename=self.filename, description=self.description, url=self.url)

    @classmethod
    def json_load(cls, file: IO):
        file_metatadata = json.load(file)
        metadata = FileMetadata(file_metatadata)
        return metadata
