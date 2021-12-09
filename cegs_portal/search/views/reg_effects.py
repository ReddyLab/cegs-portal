from cegs_portal.search.view_models import RegEffectSearch
from cegs_portal.search.views.custom_views import TemplateJsonView


class RegEffectView(TemplateJsonView):
    template = "search/reg_effect.html"

    def get_template_prepare_data(self, data):
        return {"regulatory_effect": data}

    def get_data(self, re_id):
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
