from django.db import models
from wq.db.patterns import models as patterns


class AnnotatedModel(patterns.AnnotatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class IdentifiedModel(patterns.IdentifiedModel):
    name = models.CharField(max_length=255)


class IdentifiedAnnotatedModel(
        patterns.IdentifiedModel, patterns.AnnotatedModel):
    name = models.CharField(max_length=255)


class MarkedModel(patterns.MarkedModel):
    name = models.CharField(max_length=255)


class LocatedModel(patterns.LocatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class RelatedModel(patterns.RelatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class AnotherRelatedModel(patterns.RelatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class IdentifiedRelatedModel(patterns.IdentifiedRelatedModel):
    name = models.CharField(max_length=255)


class IdentifiedMarkedModel(patterns.IdentifiedMarkedModel):
    name = models.CharField(max_length=255)


class NaturalKeyParent(patterns.NaturalKeyModel):
    code = models.CharField(max_length=10)
    group = models.CharField(max_length=10)

    class Meta:
        unique_together = ['code', 'group']


class NaturalKeyChild(patterns.NaturalKeyModel):
    parent = models.ForeignKey(NaturalKeyParent)
    mode = models.CharField(max_length=10)

    class Meta:
        unique_together = ['parent', 'mode']


class ModelWithNaturalKey(models.Model):
    key = models.ForeignKey(NaturalKeyChild)
    value = models.CharField(max_length=10)
