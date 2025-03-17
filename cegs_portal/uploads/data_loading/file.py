import json
import os
from typing import IO, Optional

from cegs_portal.search.models import File


class Metadata:
    description: Optional[str]
    filename: str
    file_location: str
    url: Optional[str]

    def __init__(self, file_metadata: dict[str, str]):
        self.description = file_metadata.get("description")
        self.filename = file_metadata["filename"]
        self.file_location = file_metadata["file_location"]
        self.url = file_metadata.get("url")
        self.source_file_id = None

    def db_save(self, experiment=None, analysis=None):
        source_file = File(
            description=self.description,
            experiment=experiment,
            analysis=analysis,
            filename=self.filename,
            location=self.file_location,
            url=self.url,
        )
        source_file.save()
        self.source_file_id = source_file.id

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
        if self.source_file is not None:
            return self.source_file

        return File.objects.get(filename=self.filename, description=self.description)

    @classmethod
    def json_load(cls, file: IO):
        file_metatadata = json.load(file)
        metadata = cls(file_metatadata)
        return metadata


class TestedElementsMetadata(Metadata):
    genome_assembly: str

    def __init__(self, file_metadata: dict[str, str]):
        super().__init__(file_metadata)
        self.genome_assembly = file_metadata["genome_assembly"]


class AnalysisResultsMetadata(Metadata):
    pass
