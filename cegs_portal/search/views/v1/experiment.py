from django.http import Http404

from cegs_portal.search.json_templates.v1.experiment import experiment
from cegs_portal.search.view_models.v1 import ExperimentSearch
from cegs_portal.search.views.custom_views import TemplateJsonView


class ExperimentView(TemplateJsonView):
    json_renderer = experiment
    template = "search/v1/experiment.html"
    template_data_name = "experiment"

    def get_data(self, options, exp_id):
        experi = ExperimentSearch.id_search(exp_id)

        if experi is None:
            raise Http404(f"No experiment with id {exp_id} found.")

        experi_cell_lines = set()
        experi_tissue_types = set()
        experi_assemblies = set()
        for f in experi.data_files.all():
            experi_cell_lines.update(f.cell_lines.all())
            experi_tissue_types.update(f.tissue_types.all())
            experi_assemblies.add(f"{f.ref_genome}.{f.ref_genome_patch or '0'}")

        setattr(experi, "cell_lines", experi_cell_lines)
        setattr(experi, "tissue_types", experi_tissue_types)
        setattr(experi, "assemblies", experi_assemblies)

        return experi
