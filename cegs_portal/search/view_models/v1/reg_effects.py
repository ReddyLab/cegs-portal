from typing import Optional, cast

from django.db.models import Q

from cegs_portal.search.models import (
    DNAFeature,
    RegulatoryEffectObservation,
    RegulatoryEffectObservationSet,
)
from cegs_portal.search.view_models.errors import ObjectNotFoundError


class RegEffectSearch:
    @classmethod
    def id_search(cls, re_id: str):
        reg_effect = (
            cast(RegulatoryEffectObservationSet, RegulatoryEffectObservation.objects)
            .with_facet_values()
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
    def expr_id(cls, reo_id: str) -> Optional[str]:
        reo = RegulatoryEffectObservation.objects.filter(accession_id=reo_id).values_list(
            "experiment_accession_id", flat=True
        )

        if len(reo) == 0:
            raise ObjectNotFoundError(f"Regulatory Effect Observation {reo_id} not found")

        return reo[0]

    @classmethod
    def is_public(cls, reo_id: str) -> Optional[str]:
        reo = RegulatoryEffectObservation.objects.filter(accession_id=reo_id).values_list("public", flat=True)

        if len(reo) == 0:
            raise ObjectNotFoundError(f"Regulatory Effect Observation {reo_id} not found")

        return reo[0]

    @classmethod
    def is_archived(cls, reo_id: str) -> Optional[str]:
        reo = RegulatoryEffectObservation.objects.filter(accession_id=reo_id).values_list("archived", flat=True)

        if len(reo) == 0:
            raise ObjectNotFoundError(f"Regulatory Effect Observation {reo_id} not found")

        return reo[0]

    @classmethod
    def source_search(cls, source_id: str):
        reg_effects = (
            cast(RegulatoryEffectObservationSet, RegulatoryEffectObservation.objects)
            .with_facet_values()
            .filter(sources__accession_id=source_id)
            .prefetch_related(
                "experiment",
                "sources",
                "targets",
            )
            .order_by("accession_id")
        )

        return reg_effects

    @classmethod
    def source_search_public(cls, *args, **kwargs):
        return cls.source_search(*args, *kwargs).filter(public=True, archived=False)

    @classmethod
    def source_search_with_private(cls, *args, **kwargs):
        return cls.source_search(*args[:-1], *kwargs).filter(
            Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=args[-1]))
        )

    @classmethod
    def target_search(cls, source_id: str):
        reg_effects = (
            cast(RegulatoryEffectObservationSet, RegulatoryEffectObservation.objects)
            .with_facet_values()
            .filter(targets__accession_id=source_id)
            .prefetch_related(
                "experiment",
                "sources",
                "targets",
            )
            .order_by("accession_id")
        )

        return reg_effects

    @classmethod
    def target_search_public(cls, *args, **kwargs):
        return cls.target_search(*args, *kwargs).filter(public=True, archived=False)

    @classmethod
    def target_search_with_private(cls, *args, **kwargs):
        return cls.target_search(*args[:-1], *kwargs).filter(
            Q(archived=False) & (Q(public=True) | Q(experiment_accession_id__in=args[-1]))
        )

    @classmethod
    def feature_search(cls, features: list[DNAFeature]):
        reg_effects = (
            cast(RegulatoryEffectObservationSet, RegulatoryEffectObservation.objects)
            .with_facet_values()
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
