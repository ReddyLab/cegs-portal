from django.core.paginator import Paginator
from django.http import Http404

from cegs_portal.search.json_templates.v1.experiment import experiment
from cegs_portal.search.view_models.v1 import ExperimentSearch
from cegs_portal.search.views.custom_views import TemplateJsonView


class ExperimentView(TemplateJsonView):
    json_renderer = experiment
    template = "search/v1/experiment.html"

    def get(self, request, options, data, exp_id):
        return super().get(
            request,
            options,
            {
                "experiment": data[0],
                "other_experiments": {
                    "id": "other_experiments",
                    "options": [{"value": e.accession_id, "text": f"{e.accession_id}: {e.name}"} for e in data[1]],
                },
            },
        )

    def get_json(self, request, options, data, exp_id):
        return super().get_json(request, options, data[0])

    def get_data(self, options, exp_id):
        experi = ExperimentSearch.accession_search(exp_id)
        other_experiments = ExperimentSearch.all_except(exp_id)

        if experi is None:
            raise Http404(f"No experiment with id {exp_id} found.")

        experi_assemblies = set()
        for f in experi.data_files.all():
            experi_assemblies.add(f"{f.ref_genome}.{f.ref_genome_patch or '0'}")

        experi_cell_lines = set()
        experi_tissue_types = set()
        for bios in experi.biosamples.all():
            experi_cell_lines.add(bios.cell_line_name)
            experi_tissue_types.add(bios.cell_line.tissue_type_name)

        setattr(experi, "cell_lines", experi_cell_lines)
        setattr(experi, "tissue_types", experi_tissue_types)
        setattr(experi, "assemblies", experi_assemblies)

        return experi, other_experiments


class ExperimentListView(TemplateJsonView):
    json_renderer = experiment
    template = "search/v1/experiment_list.html"
    template_data_name = "experiments"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
        """
        options = super().request_options(request)
        options["page"] = int(request.GET.get("page", 1))
        return options

    def get_data(self, options):
        experiments = ExperimentSearch.all()
        experiments_paginator = Paginator(experiments, 20)
        experiments_page = experiments_paginator.get_page(options["page"])
        return experiments_page
