import json
import os
from typing import IO, Any, Dict, Optional

from cegs_portal.search.models import File

from .biosample import ExperimentBiosample


class FileMetadata:
    description: Optional[str]
    filename: str
    file_location: str
    genome_assembly: str
    url: Optional[str]
    misc: dict[str, Any]
    id_: Optional[int] = None
    biosample: Optional[ExperimentBiosample] = None

    def __init__(
        self,
        file_metadata: Dict[str, str],
        biosamples: Optional[list[ExperimentBiosample]] = None,
    ):
        self.description = file_metadata.get("description")
        self.filename = file_metadata["file_name"]
        self.file_location = file_metadata["file_location"]
        self.genome_assembly = file_metadata["genome_assembly"]
        self.url = file_metadata.get("url")
        self.misc = file_metadata.get("misc")

        if biosamples is not None:
            biosample_index = file_metadata.get("biosample", 0)
            self.biosample = biosamples[biosample_index]

    def db_save(self, experiment=None, analysis=None, experiment_data_file=None):
        source_file = File(
            description=self.description,
            experiment=experiment,
            data_file_info=experiment_data_file,
            analysis=analysis,
            filename=self.filename,
            location=self.file_location,
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
