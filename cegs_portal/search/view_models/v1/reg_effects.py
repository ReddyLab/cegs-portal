from django.db.models import Q

from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation


class RegEffectSearch:
    @classmethod
    def id_search(cls, re_id: str):
        reg_effect = (
            RegulatoryEffectObservation.objects.with_facet_values()
            .filter(accession_id=re_id)
            .prefetch_related(
                "experiment",
                "experiment__biosamples",
                "experiment__biosamples__cell_line",
                "sources",
                "targets",
            )
            .first()
        )
        return reg_effect

    @classmethod
    def source_search(cls, source_id: str):
        reg_effects = (
            RegulatoryEffectObservation.objects.with_facet_values()
            .filter(sources__accession_id=source_id)
            .prefetch_related(
                "experiment__biosamples__cell_line",
                "sources__source_for",
                "targets__target_of__sources",
            )
        )

        return reg_effects

    @classmethod
    def feature_search(cls, features: list[DNAFeature]):
        reg_effects = (
            RegulatoryEffectObservation.objects.with_facet_values()
            .filter(Q(sources__in=features) | Q(targets__in=features))
            .prefetch_related(
                "targets",
                "targets__target_of",
                "targets__target_of__sources",
                "experiment",
                "sources",
                "sources__source_for",
            )
        )

        return reg_effects
