from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from cegs_portal.search.views.renderers import json
from cegs_portal.search.views.view_utils import JSON_MIME


class TemplateJsonView(View):
    json_renderer = json
    template = None

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method.lower() in self.http_method_names:
            data_handler = getattr(self, f"{request.method.lower()}_data", None)
            if request.headers.get("accept") == JSON_MIME or request.GET.get("accept", None) == JSON_MIME:
                handler_name = f"{request.method.lower()}_json"
            else:
                handler_name = request.method.lower()
            handler = getattr(self, handler_name, self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, data_handler, *args, **kwargs)

    def get_template_prepare_data(self, data):
        return {"results": data}

    def get(self, request, data_handler, *args, **kwargs):
        return render(request, self.template, self.get_template_prepare_data(data_handler(*args, **kwargs)))

    def get_json(self, request, data_handler, *args, **kwargs):
        return JsonResponse(TemplateJsonView.json_renderer(data_handler(*args, **kwargs)), safe=False)
