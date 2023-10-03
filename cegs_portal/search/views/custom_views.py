import csv
import io
import logging
from typing import Any, Callable, Optional

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import BadRequest
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View

from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME, TSV_MIME
from cegs_portal.utils.http_exceptions import Http303, Http400, Http500
from cegs_portal.utils.http_responses import HttpResponseSeeOtherRedirect

logger = logging.getLogger("django.request")


class TsvResponse(HttpResponse):
    def __init__(
        self,
        data,
        filename,
        **kwargs,
    ):
        headers = kwargs.get("headers", {})
        if filename is None:
            headers["Content-Disposition"] = 'attachment; filename="data.tsv"'
        else:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        kwargs["headers"] = headers

        super().__init__(content_type="text/tab-separated-values", **kwargs)

        with io.StringIO() as csv_output:
            tsvwriter = csv.writer(csv_output, delimiter="\t")
            for row in data:
                tsvwriter.writerow(row)
            csv_string = csv_output.getvalue()

        self.content = csv_string


class ExperimentAccessMixin(UserPassesTestMixin):
    request: Any

    def test_func(self):
        if self.is_archived():
            self.raise_exception = True
            return False

        if self.is_public():
            return True

        if self.request.user.is_anonymous:
            return False

        return (
            self.request.user.is_superuser
            or self.request.user.is_portal_admin
            or self.get_experiment_accession_id() in self.request.user.all_experiments()
        )

    def is_archived(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is missing the implementation of the is_archived() method."
        )

    def is_public(self):
        raise NotImplementedError(f"{self.__class__.__name__} is missing the implementation of the is_public() method.")

    def get_experiment_accession_id(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} is missing the implementation of the get_experiment_accession_id() method."
        )


def default_tsv_renderer(data):
    raise NotImplementedError("FeatureEffectsView.get_data")


class TemplateJsonView(View):
    json_renderer: Callable = json
    tsv_renderer: Callable = default_tsv_renderer
    template: Optional[str] = None
    template_data_name: Optional[str] = None

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.

        try:
            options = self.request_options(request)
        except Http400 as err:
            self.http_bad_request(request, err)

        if request.method.lower() in self.http_method_names:
            data_handler = getattr(self, f"{request.method.lower()}_data", None)
            match options["format"]:
                case "json":
                    handler_name = f"{request.method.lower()}_json"
                case "tsv":
                    handler_name = f"{request.method.lower()}_tsv"
                case "html":
                    handler_name = request.method.lower()

            handler = getattr(self, handler_name, self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        response = None
        try:
            assert data_handler is not None
            response = handler(request, options, data_handler(options, *args, **kwargs), *args, **kwargs)
        except Http303 as redirect:
            response = HttpResponseSeeOtherRedirect(redirect_to=redirect.location)
        except Http400 as err:
            self.http_bad_request(request, err)

        if response is None:
            raise Http500("Custom response is None")

        return response

    def request_options(self, request):
        if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
            return {
                "format": "json",
                "json_format": request.GET.get("format", None),
            }

        if request.headers.get("accept") == TSV_MIME or request.GET.get("accept", None) == TSV_MIME:
            return {"format": "tsv"}

        return {"format": "html"}

    def get(self, request, _options, data, *args, **kwargs):
        if self.__class__.template_data_name is not None:
            data = {self.__class__.template_data_name: data}

        if self.template is not None:
            return render(
                request,
                self.template,
                data,
            )

        raise Http500("No template found")

    def get_json(self, _request, options, data, *args, **kwargs):
        return JsonResponse(self.__class__.json_renderer(data, options), safe=False)

    def get_tsv(self, _request, _options, data, *args, **kwargs):
        filename = kwargs.get("filename", None)
        return TsvResponse(self.__class__.tsv_renderer(data), filename)

    def post(self, request, _options, data, *args, **kwargs):
        if self.__class__.template_data_name is not None:
            data = {self.__class__.template_data_name: data}

        if self.template is not None:
            return render(
                request,
                self.template,
                data,
            )

        raise Http500("No template found")

    def post_json(self, _request, options, data, *args, **kwargs):
        return JsonResponse(self.__class__.json_renderer(data, options), safe=False)

    def http_bad_request(self, request, err, *args, **kwargs):
        raise BadRequest() from err
