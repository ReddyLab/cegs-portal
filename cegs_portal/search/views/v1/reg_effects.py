from cegs_portal.search.view_models.v1 import RegEffectSearch
from cegs_portal.search.views.custom_views import TemplateJsonView


class RegEffectView(TemplateJsonView):
    template = "search/v1/reg_effect.html"
    template_data_name = "regulatory_effect"

    def get_data(self, _options, re_id):
        """
        Headers used:
            accept
                * application/json
        """
        search_results = RegEffectSearch.id_search(re_id)

        cell_lines = set()
        tissue_types = set()
        for f in search_results.experiment.data_files.all():
            cell_lines.update(f.cell_lines.all())
            tissue_types.update(f.tissue_types.all())
        setattr(search_results, "cell_lines", cell_lines)
        setattr(search_results, "tissue_types", tissue_types)

        return search_results
