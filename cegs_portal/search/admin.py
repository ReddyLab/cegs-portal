from django.contrib import admin

from .models import DNaseIHypersensitiveSite, RegulatoryEffect

admin.site.register(DNaseIHypersensitiveSite)
admin.site.register(RegulatoryEffect)
