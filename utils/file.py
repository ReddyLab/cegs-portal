import json
import os.path
from typing import Dict

from cegs_portal.search.models import File


class FileMetadata:
    data_filename: str
    description: str
    url: str

    def __init__(self, file_metadata: Dict[str, str], filename):
        self.data_filename = file_metadata["file"]
        self.description = file_metadata["description"]
        self.filename = filename
        self.url = file_metadata["url"]

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
    def json_load(cls, file):
        file_metatadata = json.load(file)
        metadata = FileMetadata(file_metatadata, file.name)
        return metadata
