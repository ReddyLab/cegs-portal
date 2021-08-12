from django.db import models


class Experiment(models.Model):
    name = models.CharField(max_length=512)
