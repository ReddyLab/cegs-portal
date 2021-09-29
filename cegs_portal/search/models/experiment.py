from django.db import models


class Experiment(models.Model):
    name = models.CharField(max_length=512)
    data_files = models.ManyToManyField("ExperimentDataFile", related_name="experiment_set")


class ExperimentDataFile(models.Model):
    cell_line = models.CharField(max_length=100)
    experiment = models.ForeignKey("Experiment", on_delete=models.CASCADE)
    filename = models.CharField(max_length=512)
    ref_genome = models.CharField(max_length=20)
    ref_genome_patch = models.CharField(max_length=10)
    significance_measure = models.CharField(max_length=2048)
