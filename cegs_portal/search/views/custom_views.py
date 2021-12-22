import logging

from django.http import Http404, HttpResponseNotFound
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME

logger = logging.getLogger("django.request")


class TemplateJsonView(View):
    json_renderer = json
    template = None
    template_data_name = None

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.

        options = self.request_options(request)

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
        except Http404 as err:
            response = self.http_page_not_found(request, err)

        return response

    def request_options(self, request):
        options = {
            "is_json": False,
        }

        if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
            options["is_json"] = True

        options["json_format"] = request.GET.get("format", None)

        return options

    def get(self, request, options, data, *args, **kwargs):
        if self.__class__.template_data_name is not None:
            data = {self.__class__.template_data_name: data}

        return render(
            request,
            self.template,
            data,
        )

    def get_json(self, _request, options, data, *args, **kwargs):
        return JsonResponse(self.__class__.json_renderer(data, options.get("json_format", None)), safe=False)

    def http_page_not_found(self, request, err, *args, **kwargs):
        logger.warning(
            "Response Not Found (%s): %s", request.method, request.path, extra={"status_code": 404, "request": request}
        )
        return HttpResponseNotFound(str(err), *args, **kwargs)
