import factory
from factory import post_generation
from factory.django import DjangoModelFactory

from cegs_portal.search.models import RegulatoryEffect
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory


class RegEffectFactory(DjangoModelFactory):
    class Meta:
        model = RegulatoryEffect

    experiment = factory.SubFactory(ExperimentFactory)

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
            for feature in extracted:
                self.targets.add(feature)  # pylint: disable=no-member

    @post_generation
    def target_assemblies(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for assembly in extracted:
                self.target_assemblies.add(assembly)  # pylint: disable=no-member

    @post_generation
    def facet_values(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for value in extracted:
                self.facet_values.add(value)  # pylint: disable=no-member
