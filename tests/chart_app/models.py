from django.db import models
from wq.db.patterns import models as patterns


class Series(patterns.IdentifiedModel):
    name = models.CharField(max_length=20)


class Value(models.Model):
    series = models.ForeignKey(Series)
    date = models.DateField()
    parameter = models.CharField(max_length=20)
    units = models.CharField(max_length=20)
    value = models.FloatField()
