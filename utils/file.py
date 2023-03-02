import json
from typing import IO, Dict, Optional

from cegs_portal.search.models import File


class FileMetadata:
    description: Optional[str]
    filename: str
    url: Optional[str]

    def __init__(self, file_metadata: Dict[str, str]):
        self.description = file_metadata.get("description", None)
        self.filename = file_metadata["file"]
        self.url = file_metadata.get("url", None)

    def db_save(self, experiment):
        source_file = File(
            description=self.description,
            experiment=experiment,
            filename=self.filename,
            url=self.url,
        )
        source_file.save()

        return source_file

    def db_del(self):
        self.file.delete()

    @property
    def file(self):
        return File.objects.get(filename=self.filename, description=self.description, url=self.url)

    @classmethod
    def json_load(cls, file: IO):
        file_metatadata = json.load(file)
        metadata = FileMetadata(file_metatadata)
        return metadata
