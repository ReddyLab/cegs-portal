from django.db import models


# Create your models here.
class QueryCache(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    value = models.JSONField(null=True, blank=True)
