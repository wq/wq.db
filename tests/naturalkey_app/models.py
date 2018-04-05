from django.db import models
from natural_keys.models import NaturalKeyModel


class NaturalKeyParent(NaturalKeyModel):
    slug = models.SlugField()

    def __str__(self):
        return self.slug

    class Meta:
        unique_together = [['slug']]


class NaturalKeyChild(NaturalKeyModel):
    date = models.DateField()
    parent = models.ForeignKey(NaturalKeyParent, models.CASCADE)

    def __str__(self):
        return "%s on %s" % (self.parent, self.date)

    class Meta:
        unique_together = [['parent', 'date']]


class ModelWithNaturalKey(models.Model):
    key = models.ForeignKey(NaturalKeyChild, models.CASCADE)
    note = models.TextField()

    def __str__(self):
        return "%s: %s" % (self.key, self.note)
