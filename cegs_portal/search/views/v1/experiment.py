from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import render

from cegs_portal.search.json_templates.v1.experiment import experiment, experiments
from cegs_portal.search.models.validators import validate_accession_id
from cegs_portal.search.validators import validate_analysis_accession_id
from cegs_portal.search.view_models.errors import ObjectNotFoundError
from cegs_portal.search.view_models.v1 import ExperimentSearch
from cegs_portal.search.views.custom_views import (
    ExperimentAccessMixin,
    MultiResponseFormatView,
)
from cegs_portal.users.models import UserType
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
        return False  # it's okay to see archived experiments

    def request_options(self, request):
        """
        GET queries used:
            analysis (single)
                * Should be a valid analysis accession ID
        """
        options = super().request_options(request)
        options["analysis"] = request.GET.get("analysis", None)
        if options["analysis"] is not None:
            validate_analysis_accession_id(options["analysis"])

        return options

    def get(self, request, options, data, exp_id):
        experiment, related_experiments = data
        analyses = list(ExperimentSearch.all_analysis_id_search(exp_id))
        analyses_list = []

        if options["analysis"] is not None:
            analysis_selected = options["analysis"]
        else:
            analysis_selected = ExperimentSearch.default_analysis_id_search(exp_id)

        for analysis in analyses:
            if analysis == options["analysis"]:
                analyses_list.append(("selected", analysis))
            else:
                analyses_list.append(("", analysis))

        related_experiments = [
            {
                "name": r.other_experiment.name,
                "other_experiment_id": r.other_experiment_id,
                "description": r.description if r.description != "" else "No Description",
            }
            for r in related_experiments
        ]
        return super().get(
            request,
            options,
            {
                "logged_in": not request.user.is_anonymous,
                "analyses": analyses_list,
                "analysis_selected": analysis_selected,
                "experiment": experiment,
                "related_experiments": related_experiments,
            },
        )

    def get_json(self, request, options, data, exp_id):
        return super().get_json(request, options, data[0])

    def get_data(self, options, exp_id):
        experi = ExperimentSearch.accession_search(exp_id)

        if experi is None:
            raise Http404(f"No experiment with id {exp_id} found.")

        if self.request.user.is_anonymous:
            related_experiments = ExperimentSearch.related_experiments(exp_id, UserType.ANONYMOUS)
        elif self.request.user.is_superuser or self.request.user.is_portal_admin:
            related_experiments = ExperimentSearch.related_experiments(exp_id, UserType.ADMIN)

        else:
            related_experiments = ExperimentSearch.related_experiments(
                exp_id, UserType.LOGGED_IN, self.request.user.all_experiments()
            )

        experi_cell_lines = set()
        experi_tissue_types = set()
        for bios in experi.biosamples.all():
            experi_cell_lines.add(bios.cell_line_name)
            experi_tissue_types.add(bios.cell_line.tissue_type_name)

        setattr(experi, "cell_lines", experi_cell_lines)
        setattr(experi, "tissue_types", experi_tissue_types)
        setattr(experi, "genome_assembly", experi.default_analysis.genome_assembly)

        return experi, related_experiments


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
                        "genome_assembly": exp.default_analysis.genome_assembly,
                    }
                    for exp in data.all()
                ],
            },
        )

    def get_data(self, options):
        if len(options["exp_ids"]) == 0:
            raise Http400("Please specify at least one experiment.")

        return ExperimentSearch.multi_accession_search(options["exp_ids"])


def sorted_facets(facet_values):
    facets = {}
    for value in facet_values.all():
        if value.facet.name in facets:
            facets[value.facet.name].append(value)
        else:
            facets[value.facet.name] = [value]

    sorted_facets = {}
    if "Genome Assembly" in facets:
        sorted_facets["Genome Assembly"] = facets.pop("Genome Assembly")

    sorted_facets.update(facets)
    return sorted_facets


class ExperimentListView(MultiResponseFormatView):
    json_renderer = experiments
    template = "search/v1/experiment_list.html"
    table_partial = "search/v1/partials/_experiment_list.html"

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
            coll_facet (multiple)
                * Should match a categorical facet value
        """
        options = super().request_options(request)
        options["facets"] = [int(facet) for facet in request.GET.getlist("facet", [])]
        options["coll_facets"] = [int(facet) for facet in request.GET.getlist("coll_facet", [])]
        return options

    def get(self, request, options, data):
        experiment_objects, collection_objects, facet_values, collection_facet_values = data

        sorted_exp_facets = sorted_facets(facet_values)
        sorted_coll_facets = sorted_facets(collection_facet_values)

        if request.headers.get("HX-Target") == "multi-exp-modal-container":
            return render(
                request,
                "search/v1/partials/_multi_experiment_index.html",
                {
                    "experiments": experiment_objects,
                    "collections": collection_objects,
                    "facets": sorted_exp_facets,
                    "collection_facets": sorted_coll_facets,
                },
            )

        if request.headers.get("HX-Target") == "modal-container":
            return render(
                request,
                "search/v1/partials/_experiment_index.html",
                {
                    "experiments": experiment_objects,
                    "collections": collection_objects,
                    "facets": sorted_exp_facets,
                    "collection_facets": sorted_coll_facets,
                },
            )

        if request.headers.get("HX-Target") == "experiment-list":
            return render(
                request,
                self.table_partial,
                {
                    "experiments": experiment_objects,
                },
            )

        if request.headers.get("HX-Target") == "experiment-collection-list":
            return render(
                request,
                "search/v1/partials/_experiment_collection_list.html",
                {
                    "collections": collection_objects,
                },
            )

        return super().get(
            request,
            options,
            {
                "logged_in": not request.user.is_anonymous,
                "experiments": experiment_objects,
                "collections": collection_objects,
                "facets": sorted_exp_facets,
                "collection_facets": sorted_coll_facets,
            },
        )

    def get_data(self, options):
        facet_values = ExperimentSearch.experiment_facet_values()
        collection_facet_values = ExperimentSearch.experiment_collection_facet_values()

        if self.request.user.is_anonymous:
            return (
                ExperimentSearch.experiments(options["facets"], UserType.ANONYMOUS),
                ExperimentSearch.collections(options["coll_facets"], UserType.ANONYMOUS),
                facet_values,
                collection_facet_values,
            )

        if self.request.user.is_superuser or self.request.user.is_portal_admin:
            return (
                ExperimentSearch.experiments(options["facets"], UserType.ADMIN),
                ExperimentSearch.collections(options["coll_facets"], UserType.ADMIN),
                facet_values,
                collection_facet_values,
            )

        return (
            ExperimentSearch.experiments(options["facets"], UserType.LOGGED_IN, self.request.user.all_experiments()),
            ExperimentSearch.collections(
                options["coll_facets"], UserType.LOGGED_IN, self.request.user.all_experiment_collections()
            ),
            facet_values,
            collection_facet_values,
        )
