from typing import Union, cast

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import URLPattern, URLResolver, include, path
from django.views import defaults as default_views
from django.views.generic import RedirectView, TemplateView

import cegs_portal.search.views

urlpatterns: list[Union[URLPattern, URLResolver]] = cast(
    list[Union[URLPattern, URLResolver]],
    [
        path("", cegs_portal.search.views.index, name="home"),
        path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
        path("about/licenses/", TemplateView.as_view(template_name="pages/licenses.html"), name="licenses"),
        path(
            "about/licenses/genoverse/",
            TemplateView.as_view(template_name="pages/genoverse_license.html"),
            name="genoverse_license",
        ),
        path(
            "help/",
            include(
                [
                    path("", TemplateView.as_view(template_name="pages/help/index.html"), name="help"),
                    path(
                        "metadata/",
                        TemplateView.as_view(template_name="pages/help/data_metadata.html"),
                        name="metadata",
                    ),
                    path(
                        "data_prep/", TemplateView.as_view(template_name="pages/help/data_prep.html"), name="data_prep"
                    ),
                ]
            ),
        ),
        # Django Admin, use {% url 'admin:index' %}
        path(settings.ADMIN_URL, admin.site.urls),
        # User management
        path("users/", include("cegs_portal.users.urls", namespace="users")),
        path("accounts/", include("allauth.urls")),
        path("search/", include("cegs_portal.search.urls")),
        path("exp_data/", include("cegs_portal.get_expr_data.urls")),
        path("uploads/", include("cegs_portal.uploads.urls")),
        path("task_status/", include("cegs_portal.task_status.urls")),
        path("igvf/", include("cegs_portal.igvf.urls")),
        path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("images/favicons/favicon.ico"))),
        path("", include("django_prometheus.urls")),
    ],
) + cast(list[Union[URLPattern, URLResolver]], static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
if settings.DEBUG:
    # Static file serving when using Gunicorn + Uvicorn for local web socket development
    urlpatterns += cast(list[Union[URLPattern, URLResolver]], staticfiles_urlpatterns())


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += cast(
        list[Union[URLPattern, URLResolver]],
        [
            path(
                "400/",
                default_views.bad_request,
                kwargs={"exception": Exception("Bad Request!")},
            ),
            path(
                "403/",
                default_views.permission_denied,
                kwargs={"exception": Exception("Permission Denied")},
            ),
            path(
                "404/",
                default_views.page_not_found,
                kwargs={"exception": Exception("Page not Found")},
            ),
            path("500/", default_views.server_error),
        ],
    )
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = (
            cast(list[Union[URLPattern, URLResolver]], [path("__debug__/", include(debug_toolbar.urls))]) + urlpatterns
        )
