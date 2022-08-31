import factory
from factory import Faker
from factory.django import DjangoModelFactory

from cegs_portal.search.models import Facet, FacetType, FacetValue


class FacetFactory(DjangoModelFactory):
    class Meta:
        model = Facet

    description = Faker("text", max_nb_chars=4096)
    name = Faker("text", max_nb_chars=256)
    facet_type = FacetType.DISCRETE


class FacetValueFactory(DjangoModelFactory):
    class Meta:
        model = FacetValue

    value = Faker("text", max_nb_chars=50)
    facet = factory.SubFactory(FacetFactory)
