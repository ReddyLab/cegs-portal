from factory import Faker
from factory.django import DjangoModelFactory

from cegs_portal.search.models import File


class FileFactory(DjangoModelFactory):
    class Meta:
        model = File

    filename = Faker("file_path")
    description = Faker("text", max_nb_chars=4096)
    url = Faker("uri")
