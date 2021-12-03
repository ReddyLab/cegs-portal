from cegs_portal.search.models.reg_effects import RegulatoryEffect


class RegEffectSearch:
    @classmethod
    def id_search(cls, re_id: str):
        reg_effect = (
            RegulatoryEffect.objects.filter(id=int(re_id))
            .prefetch_related(
                "experiment",
                "sources",
                "targets",
                "targets__assemblies",
            )
            .first()
        )
        return reg_effect
