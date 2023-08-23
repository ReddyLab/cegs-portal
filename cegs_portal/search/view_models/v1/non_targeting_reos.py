from enum import Enum
from typing import Any, Optional, cast

from django.db.models import Q, QuerySet, Subquery
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    DNAFeature,
    DNAFeatureType,
    IdType,
    RegulatoryEffectObservation,
    RegulatoryEffectObservationSet,
)
from cegs_portal.search.view_models.errors import ObjectNotFoundError, ViewModelError
from cegs_portal.utils.http_exceptions import Http500

class DNAFeatureNonTargetSearch:
    @classmethod
    def is_public(cls, feature_id: str) -> bool:
        if feature_id.startswith("DCP"):
            feature = DNAFeature.objects.filter(accession_id=feature_id).values_list("public", flat=True)
        elif feature_id.startswith("ENS"):
            feature = DNAFeature.objects.filter(ensembl_id=feature_id).values_list("public", flat=True)
        else:
            feature = DNAFeature.objects.filter(name__iexact=feature_id).values_list("public", flat=True)

        if len(feature) == 0:
            raise ObjectNotFoundError(f"DNA Feature {feature_id} not found")

        return cast(bool, feature[0])

    @classmethod
    def is_archived(cls, feature_id: str) -> bool:
        if feature_id.startswith("DCP"):
            feature = DNAFeature.objects.filter(accession_id=feature_id).values_list("archived", flat=True)
        elif feature_id.startswith("ENS"):
            feature = DNAFeature.objects.filter(ensembl_id=feature_id).values_list("archived", flat=True)
        else:
            feature = DNAFeature.objects.filter(name__iexact=feature_id).values_list("archived", flat=True)

        if len(feature) == 0:
            raise ObjectNotFoundError(f"DNA Feature {feature_id} not found")

        return cast(bool, feature[0])

    @classmethod
    def id_feature_search(cls, feature_accession_id: str):

        return DNAFeature.objects.get(accession_id=feature_accession_id)

    @classmethod
    def non_targeting_regeffect_search(cls, feature_accession_id: str, sig_only: bool):
        source_features = DNAFeature.objects.filter(closest_gene__accession_id=feature_accession_id)
        reg_effects = (
            RegulatoryEffectObservation.objects.filter(
                sources__in=Subquery(source_features.values("id")), targets=None
            )
            .order_by('facet_num_values__Significance')
        )

        if sig_only:
            reg_effects = reg_effects.exclude(facet_values__value="Non-significant")

        return reg_effects.prefetch_related("sources")
