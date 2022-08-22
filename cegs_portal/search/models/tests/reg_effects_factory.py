import factory
from factory import post_generation
from factory.django import DjangoModelFactory
from faker import Faker

from cegs_portal.search.models import RegulatoryEffect
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory


class RegEffectFactory(DjangoModelFactory):
    class Meta:
        model = RegulatoryEffect

    _faker = Faker()
    experiment = factory.SubFactory(ExperimentFactory)
    facet_num_values = {
        RegulatoryEffect.Facet.EFFECT_SIZE.value: -0.0660384670056446,
        RegulatoryEffect.Facet.RAW_P_VALUE.value: 3.19229500470051e-06,
        RegulatoryEffect.Facet.SIGNIFICANCE.value: 0.000427767530629869,
    }

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.accession_id = cls._faker.unique.hexify(text="DCPRE^^^^^^^^", upper=True)
        obj.save()
        return obj

    @post_generation
    def sources(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for region in extracted:
                self.sources.add(region)  # pylint: disable=no-member

    @post_generation
    def targets(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for assembly in extracted:
                self.targets.add(assembly)  # pylint: disable=no-member

    @post_generation
    def facet_values(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for value in extracted:
                self.facet_values.add(value)  # pylint: disable=no-member
