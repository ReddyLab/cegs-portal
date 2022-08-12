from django.db.models import Q

from cegs_portal.search.models import DNAFeature, RegulatoryEffect


class RegEffectSearch:
    @classmethod
    def id_search(cls, re_id: str):
        reg_effect = (
            RegulatoryEffect.objects.with_facet_values()
            .filter(id=int(re_id))
            .prefetch_related(
                "experiment",
                "experiment__data_files",
                "experiment__data_files__cell_lines",
                "experiment__data_files__tissue_types",
                "sources",
                "target_assemblies",
            )
            .first()
        )
        return reg_effect

    @classmethod
    def region_search(cls, region_id: str):
        reg_effects = (
            RegulatoryEffect.objects.with_facet_values()
            .filter(sources__in=[int(region_id)])
            .prefetch_related(
                "experiment__data_files__cell_lines",
                "experiment__data_files__tissue_types",
                "sources__regulatory_effects",
                "target_assemblies__regulatory_effects__sources",
            )
        )

        return reg_effects

    @classmethod
    def feature_search(cls, features: list[DNAFeature]):
        reg_effects = (
            RegulatoryEffect.objects.with_facet_values()
            .filter(Q(sources__in=features) | Q(target_assemblies__in=features))
            .prefetch_related(
                "target_assemblies",
                "target_assemblies__regulatory_effects",
                "target_assemblies__regulatory_effects__sources",
                "experiment",
                "sources",
                "sources__regulatory_effects",
            )
        )

        return reg_effects
