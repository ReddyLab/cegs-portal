from django.contrib import admin

from cegs_portal.tasks.models import ThreadTask


class ThreadTaskAdmin(admin.ModelAdmin):
    list_display = ("display_name", "started_at", "ended_at", "is_done", "failed")
    search_fields = ["description"]


admin.site.register(ThreadTask, ThreadTaskAdmin)
