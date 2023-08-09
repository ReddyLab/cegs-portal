from django.contrib.admin.apps import AdminConfig


class HideAdminConfig(AdminConfig):
    default_site = "cegs_portal.hide_admin.admin_site.HideAdminSite"
