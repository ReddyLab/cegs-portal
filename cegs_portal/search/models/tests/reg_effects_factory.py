import random

import factory
from factory import post_generation
from factory.django import DjangoModelFactory

from cegs_portal.search.models import RegulatoryEffect
from cegs_portal.search.models.reg_effects import EffectDirectionType
from cegs_portal.search.models.tests.experiment_factory import ExperimentFactory


class RegEffectFactory(DjangoModelFactory):
    class Meta:
        model = RegulatoryEffect

    direction = random.choice(
        [
            EffectDirectionType.DEPLETED.value,
            EffectDirectionType.ENRICHED.value,
            EffectDirectionType.NON_SIGNIFICANT.value,
            EffectDirectionType.BOTH.value,
        ]
    )
    experiment = factory.SubFactory(ExperimentFactory)
    effect_size = random.random()
    significance = random.random()
    raw_p_value = random.random()

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
