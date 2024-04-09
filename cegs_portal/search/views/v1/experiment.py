from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404

from cegs_portal.search.json_templates.v1.experiment import experiment, experiments
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import ExperimentSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    MultiResponseFormatView,
)
from cegs_portal.utils.http_exceptions import Http400


class ExperimentView(ExperimentAccessMixin, MultiResponseFormatView):
    json_renderer = experiment
    template = "search/v1/experiment.html"

    def get_experiment_accession_id(self):
        return self.kwargs["exp_id"]

    def is_public(self):
        try:
            return ExperimentSearch.is_public(self.kwargs["exp_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def is_archived(self):
        try:
            return ExperimentSearch.is_archived(self.kwargs["exp_id"])
        except ObjectNotFoundError as e:
            raise Http404(str(e))

    def request_options(self, request):
        """
        GET queries used:
            exp (multiple)
                * Should be a valid experiment accession ID
        """
        options = super().request_options(request)
        options["analyses"] = request.GET.getlist("analysis", "vpdata.pd")

        return options

    def get(self, request, options, data, exp_id):
        analysis = ExperimentSearch.analysis_id_search(exp_id)

        return super().get(
            request,
            options,
            {
                "logged_in": not request.user.is_anonymous,
                "analysis": analysis,
                "experiment": data[0],
                "exp_id": exp_id,
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


class ExperimentsView(UserPassesTestMixin, MultiResponseFormatView):
    template = "search/v1/experiments.html"

    def test_func(self):
        experiment_ids = self.request.GET.getlist("exp", [])

        # Users have permission to request no experiments, but it is a "bad request"
        # and will be handled later on, in get_data
        if len(experiment_ids) == 0:
            return True

        for expr_id in experiment_ids:
            validate_accession_id(expr_id)

        try:
            experiments = ExperimentSearch.experiment_statuses(experiment_ids)
        except ObjectNotFoundError as e:
            raise Http404(str(e))

        if any(archived for _, _, archived in experiments):
            self.raise_exception = True  # Don't redirect to login
            return False

        if all(public for _, public, _ in experiments):
            return True

        if self.request.user.is_anonymous:
            return False

        private_experiments = {accession_id for accession_id, public, _ in experiments if not public}

        return (
            self.request.user.is_superuser
            or self.request.user.is_portal_admin
            or private_experiments <= set(self.request.user.all_experiments())
        )

    def request_options(self, request):
        """
        GET queries used:
            exp (multiple)
                * Should be a valid experiment accession ID
        """
        options = super().request_options(request)
        options["exp_ids"] = request.GET.getlist("exp", [])
        for expr in options["exp_ids"]:
            validate_accession_id(expr)

        return options

    def get(self, request, options, data):
        return super().get(
            request,
            options,
            {
                "logged_in": not request.user.is_anonymous,
                "experiments": data,
                "experiment_viz": [
                    {
                        "accession_id": exp.accession_id,
                        "source": exp.get_source_type_display(),
                        "analysis_accession_id": exp.default_analysis.accession_id,
                    }
                    for exp in data.all()
                ],
            },
        )

    def get_data(self, options):
        if len(options["exp_ids"]) == 0:
            raise Http400("Please specify at least one experiment.")

        return ExperimentSearch.multi_accession_search(options["exp_ids"])


class ExperimentListView(MultiResponseFormatView):
    json_renderer = experiments
    template = "search/v1/experiment_list.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            facet (multiple)
                * Should match a categorical facet value
        """
        options = super().request_options(request)
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        return options

    def get(self, request, options, data):
        experiment_objects, facet_values = data

        facets = {}
        for value in facet_values.all():
            if value.facet.name in facets:
                facets[value.facet.name].append(value)
            else:
                facets[value.facet.name] = [value]

        return super().get(
            request,
            options,
            {
                "logged_in": not request.user.is_anonymous,
                "experiments": experiment_objects,
                "experiment_ids": [expr.accession_id for expr in experiment_objects],
                "facets": facets,
            },
        )

    def get_data(self, options):
        facet_values = ExperimentSearch.experiment_facet_values()

        if self.request.user.is_anonymous:
            return ExperimentSearch.all_public(options["facets"]), facet_values

        if self.request.user.is_superuser or self.request.user.is_portal_admin:
            return ExperimentSearch.all(options["facets"]), facet_values

        return ExperimentSearch.all_with_private(options["facets"], self.request.user.all_experiments()), facet_values
