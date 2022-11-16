import logging
from typing import Callable, Optional

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME
from cegs_portal.utils.http_exceptions import Http400, Http500

logger = logging.getLogger("django.request")


class ExperimentAccessMixin(UserPassesTestMixin):
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
            or self.get_experiment_accession_id() in self.request.user.experiments
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


class TemplateJsonView(View):
    json_renderer: Callable = json
    template: Optional[str] = None
    template_data_name: Optional[str] = None

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.

        try:
            options = self.request_options(request)
        except Http400 as err:
            return self.http_bad_request(request, err)
        except Http404 as err:
            return self.http_page_not_found(request, err)
        except Http500 as err:
            return self.http_internal_error(request, err)

        if request.method.lower() in self.http_method_names:
            data_handler = getattr(self, f"{request.method.lower()}_data", None)
            if options["is_json"]:
                handler_name = f"{request.method.lower()}_json"
            else:
                handler_name = request.method.lower()
            handler = getattr(self, handler_name, self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        try:
            response = handler(request, options, data_handler(options, *args, **kwargs), *args, **kwargs)
        except Http400 as err:
            response = self.http_bad_request(request, err)
        except Http404 as err:
            response = self.http_page_not_found(request, err)
        except Http500 as err:
            response = self.http_internal_error(request, err)

        return response

    def request_options(self, request):
        return {
            "is_json": request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME,
            "json_format": request.GET.get("format", None),
        }

    def get(self, request, options, data, *args, **kwargs):
        if self.__class__.template_data_name is not None:
            data = {self.__class__.template_data_name: data}

        if self.template is not None:
            return render(
                request,
                self.template,
                data,
            )

        return self.http_internal_error(request, "No template found")

    def get_json(self, _request, options, data, *args, **kwargs):
        return JsonResponse(self.__class__.json_renderer(data, options), safe=False)

    def post(self, request, options, data, *args, **kwargs):
        if self.__class__.template_data_name is not None:
            data = {self.__class__.template_data_name: data}

        if self.template is not None:
            return render(
                request,
                self.template,
                data,
            )

        return self.http_internal_error(request, "No template found")

    def post_json(self, _request, options, data, *args, **kwargs):
        return JsonResponse(self.__class__.json_renderer(data, options), safe=False)

    def http_bad_request(self, request, err, *args, **kwargs):
        logger.warning(
            "400 Bad Request (%s): %s",
            request.method,
            request.path,
            extra={"status_code": 400, "request": request},
        )
        return HttpResponseBadRequest(str(err), *args, **kwargs)

    def http_page_not_found(self, request, err, *args, **kwargs):
        logger.warning(
            "404 Response Not Found (%s): %s",
            request.method,
            request.path,
            extra={"status_code": 404, "request": request},
        )
        return HttpResponseNotFound(str(err), *args, **kwargs)

    def http_internal_error(self, request, err, *args, **kwargs):
        logger.warning(
            "500 Internal Error (%s): %s", request.method, request.path, extra={"status_code": 500, "request": request}
        )
        return HttpResponseServerError(str(err), *args, **kwargs)
