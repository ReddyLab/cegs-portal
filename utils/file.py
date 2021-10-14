import json
import os.path
from typing import IO, Dict, Optional

from cegs_portal.search.models import File


class FileMetadata:
    data_filename: str
    description: Optional[str]
    filename: str  # Used only for full_data_filepath
    url: Optional[str]

    def __init__(self, file_metadata: Dict[str, str], filename):
        self.data_filename = file_metadata["file"]
        self.description = file_metadata.get("description", None)
        self.filename = filename
        self.url = file_metadata.get("url", None)

    def db_save(self):
        source_file = File(
            filename=self.data_filename,
            description=self.description,
            url=self.url,
        )
        source_file.save()
        return source_file

    @property
    def full_data_filepath(self):
        base_path = os.path.dirname(self.filename)
        return os.path.join(base_path, self.data_filename)

    @classmethod
    def json_load(cls, file: IO):
        file_metatadata = json.load(file)
        metadata = FileMetadata(file_metatadata, file.name)
        return metadata
