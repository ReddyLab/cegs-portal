from cegs_portal.search.json_templates.v1.feature_exact import feature_exact
from cegs_portal.search.json_templates.v1.features import features
from cegs_portal.search.view_models.v1 import FeatureSearch, IdType
from cegs_portal.search.views.custom_views import TemplateJsonView


class FeatureEnsembl(TemplateJsonView):
    json_renderer = feature_exact
    template = "search/v1/feature_exact.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            search_type
                * exact
                * like
                * start
                * in
        """
        options = super().request_options(request)
        options["search_type"] = request.GET.get("search_type", "exact")
        return options

    def get(self, request, options, data, feature_id):
        return super().get(request, options, {"feature": data, "feature_name": data.feature_type.capitalize()})

    def get_data(self, options, feature_id):
        features = FeatureSearch.id_search(IdType.ENSEMBL.value, feature_id, options["search_type"])
        return features.first()


class Feature(TemplateJsonView):
    json_renderer = features
    template = "search/v1/features.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            search_type
                * exact
                * like
                * start
                * in
        """
        options = super().request_options(request)
        options["search_type"] = request.GET.get("search_type", "exact")
        options["feature_types"] = request.GET.get("feature_type", ["gene"])
        return options

    def get(self, request, options, data, id_type, feature_id):
        return super().get(request, options, {"features": data, "feature_name": "Genome Features"})

    def get_data(self, options, id_type, feature_id):
        features = FeatureSearch.id_search(id_type, feature_id, options["search_type"])
        return {f: list(f.assemblies.all()) for f in features.all()}


class FeatureLoc(TemplateJsonView):
    json_renderer = features
    template = "search/v1/features.html"

    def request_options(self, request):
        """
        Headers used:
            accept
                * application/json
        GET queries used:
            accept
                * application/json
            format
                * genoverse
            search_type
                * exact
                * overlap
            assembly
                * free-text, but should match a genome assembly that exists in the DB
        """
        options = super().request_options(request)
        options["search_type"] = request.GET.get("search_type", "overlap")
        options["assembly"] = request.GET.get("assembly", None)
        options["feature_types"] = request.GET.getlist("feature_type", ["gene"])

        return options

    def get_template_prepare_data(self, data, options, chromo, start, end):
        return {"features": data, "feature_name": "Genome Features"}

    def get_data(self, options, chromo, start, end):
        if chromo.isnumeric():
            chromo = f"chr{chromo}"

        assemblies = FeatureSearch.loc_search(
            chromo, start, end, options["assembly"], options["feature_types"], options["search_type"]
        )

        features_dict = {}
        for assembly in assemblies.all():
            feature_list = features_dict.get(assembly.feature, [])
            feature_list.append(assembly)
            features_dict[assembly.feature] = feature_list

        return features_dict
