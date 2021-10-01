from django.db import models


class File(models.Model):
    filename = models.CharField(max_length=512)
    description = models.CharField(max_length=4096, null=True)
    url = models.CharField(max_length=2048, null=True)
