from django.contrib import admin

from cegs_portal.search.models import DNAFeature, RegulatoryEffectObservation

admin.site.register(DNAFeature)
admin.site.register(RegulatoryEffectObservation)
