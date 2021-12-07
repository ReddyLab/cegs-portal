from cegs_portal.search.models.reg_effects import RegulatoryEffect


class RegEffectSearch:
    @classmethod
    def id_search(cls, re_id: str):
        reg_effect = (
            RegulatoryEffect.objects.filter(id=int(re_id))
            .prefetch_related(
                "experiment",
                "experiment__data_files",
                "experiment__data_files__cell_lines",
                "experiment__data_files__tissue_types",
                "sources",
                "targets",
                "targets__assemblies",
            )
            .first()
        )
        return reg_effect
