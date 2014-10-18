from wq.db.patterns import models


class Series(models.IdentifiedModel):
    name = models.CharField(max_length=20)


class Value(models.Model):
    series = models.ForeignKey(Series)
    date = models.DateField()
    parameter = models.CharField(max_length=20)
    units = models.CharField(max_length=20)
    value = models.FloatField()
