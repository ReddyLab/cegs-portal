from typing import Any, NotRequired, Optional, TypedDict

from cegs_portal.search.models import RegulatoryEffectObservation
from cegs_portal.utils.pagination_types import Pageable

ExperimentJson = TypedDict("ExperimentJson", {"accession_id": str, "name": str})
RegulatoryEffectObservationJson = TypedDict(
    "RegulatoryEffectObservationJson",
    {
        "accession_id": str,
        "direction": str,
        "effect_size": Optional[float],
        "significance": Optional[float],
        "raw_p_value": Optional[float],
        "experiment": NotRequired[ExperimentJson],
        "cell_lines": NotRequired[list[str]],
        "tissue_types": NotRequired[list[str]],
        "source_ids": list[str],
        "target_ids": list[Optional[str]],
    },
)


def non_target_regulatory_effect(
    non_target_data: tuple[Pageable[RegulatoryEffectObservation], Any], options: Optional[dict[str, Any]] = None
) -> RegulatoryEffectObservationJson:
    reg_effects, _ = non_target_data

    results: list[RegulatoryEffectObservationJson] = [
        {
            "accession_id": reg_effect.accession_id,
            "direction": reg_effect.direction,
            "effect_size": reg_effect.effect_size,
            "significance": reg_effect.significance,
            "experiment": {"accession_id": reg_effect.experiment.accession_id, "name": reg_effect.experiment.name},
            "raw_p_value": reg_effect.raw_p_value,
            "source_ids": [str(source.id) for source in reg_effect.sources.all()],
            "target_ids": [target.ensembl_id for target in reg_effect.targets.all()],
        }
        for reg_effect in reg_effects
    ]

    return {
        "object_list": results,
        "page": reg_effects.number,
        "has_next_page": reg_effects.has_next(),
        "has_prev_page": reg_effects.has_previous(),
        "num_pages": reg_effects.paginator.num_pages,
    }


def datatables_non_target_regulatory_effect(
    non_target_data: tuple[Pageable[RegulatoryEffectObservation], Any], options: Optional[dict[str, Any]] = None
) -> RegulatoryEffectObservationJson:
    reg_effects, _ = non_target_data

    # <th>Location</th>
    # <th>Effect Size</th>
    # <th>Direction</th>
    # <th>Significance</th>
    # <th>Distance from Gene</th>
    # <th>Source</th>
    # <th>Experiment</th>

    results = []
    for reg_effect in reg_effects.get_page(options["page"]):
        first_source = reg_effect.sources.all()[0]

        results.append(
            [
                f"{first_source.chrom_name}: {first_source.location.lower} - {first_source.location.upper}",
                reg_effect.effect_size,
                reg_effect.direction,
                reg_effect.significance,
                first_source.closest_gene_distance,
                first_source.get_feature_type_display(),
                {"name": reg_effect.experiment.name, "accession_id": reg_effect.experiment.accession_id},
            ]
        )

    return {
        "draw": options["draw"],
        "recordsTotal": reg_effects.count,
        "recordsFiltered": reg_effects.count,
        "data": results,
    }
