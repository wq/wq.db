from django.db import models
from wq.db.patterns import models as patterns


class AnnotatedModel(patterns.AnnotatedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class IdentifiedModel(patterns.IdentifiedModel):
    pass


class IdentifiedAnnotatedModel(patterns.IdentifiedAnnotatedModel):
    pass


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
    pass


class IdentifiedMarkedModel(patterns.IdentifiedMarkedModel):
    pass


class CustomPatternModel(models.Model):
    name = models.CharField(max_length=10)


class CustomAttachment(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(CustomPatternModel, related_name='attachments')


class CustomTypedPatternModel(models.Model):
    name = models.CharField(max_length=10)


class CustomType(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class CustomTypedAttachment(models.Model):
    name = models.CharField(max_length=10)
    type = models.ForeignKey(CustomType)
    parent = models.ForeignKey(
        CustomTypedPatternModel, related_name='attachments'
    )
