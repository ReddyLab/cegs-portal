from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


class TemplateJsonView(View):
    json_renderer = json
    template = None
    template_data_name = "data"

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
        return handler(request, options, data_handler, *args, **kwargs)

    def request_options(self, request):
        options = {
            "is_json": False,
        }

        if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
            options["is_json"] = True

        options["json_format"] = request.GET.get("format", None)

        return options

    def get_template_prepare_data(self, data, _options, *_args, **_kwargs):
        return {self.__class__.template_data_name: data}

    def get(self, request, options, data_handler, *args, **kwargs):
        return render(
            request,
            self.template,
            self.get_template_prepare_data(data_handler(options, *args, **kwargs), options, *args, **kwargs),
        )

    def get_json(self, _request, options, data_handler, *args, **kwargs):
        return JsonResponse(self.__class__.json_renderer(data_handler(options, *args, **kwargs)), safe=False)
