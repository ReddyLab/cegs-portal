from cegs_portal.search.view_models.v1 import FeatureSearch, IdType
from cegs_portal.search.views.custom_views import TemplateJsonView
from cegs_portal.search.views.renderers import json


class FeatureEnsembl(TemplateJsonView):
    template = "search/feature_exact.html"

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
        options["feature_types"] = request.GET.get("features", ["gene"])
        return options

    def get(self, request, options, data, feature_id):
        return super().get(request, options, {"feature": data, "feature_name": "Gene"})

    def get_data(self, options, feature_id):
        features = FeatureSearch.id_search(
            IdType.ENSEMBL.value, feature_id, options["feature_types"], options["search_type"]
        )
        return features.first()


class Feature(TemplateJsonView):
    template = "search/features.html"

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
        options["feature_types"] = request.GET.get("features", ["gene"])
        return options

    def get(self, request, options, data, id_type, feature_id):
        return super().get(request, options, {"features": data, "feature_name": "Genes"})

    def get_data(self, options, id_type, feature_id):
        features = FeatureSearch.id_search(id_type, feature_id, options["feature_types"], options["search_type"])
        return {f: list(f.assemblies.all()) for f in features.all()}

    def get_json(self, _request, options, data, id_type, feature_id):
        return super().get_json(_request, options, [json(result, options["json_format"]) for result in data])


class FeatureLoc(TemplateJsonView):
    template = "search/features.html"

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
        options["feature_types"] = request.GET.getlist("feature", ["gene"])

        return options

    def get_json(self, _request, options, data, chromo, start, end):
        feature_dict = [
            {
                "feature": json(f, options["json_format"]),
                "assemblies": [json(a, options["json_format"]) for a in assemblies],
            }
            for f, assemblies in data.items()
        ]
        return super().get_json(_request, options, feature_dict)

    def get_template_prepare_data(self, data, options, chromo, start, end):
        return {"features": data, "feature_name": "Genes"}

    def get_data(self, options, chromo, start, end):
        if chromo.isnumeric():
            chromo = f"chr{chromo}"

        assemblies = FeatureSearch.loc_search(
            chromo, start, end, options["assembly"], options["feature_types"], options["search_type"]
        )

        features = {}
        for assembly in assemblies.all():
            feature_list = features.get(assembly.feature, [])
            feature_list.append(assembly)
            features[assembly.feature] = feature_list

        return features
