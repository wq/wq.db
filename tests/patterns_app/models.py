from django.db import models
from wq.db.patterns import models as patterns


class IdentifiedModel(patterns.IdentifiedModel):
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


class Campaign(models.Model):
    pass


class Attribute(models.Model):
    name = models.CharField(max_length=10)
    campaign = models.ForeignKey(Campaign)
    is_active = models.BooleanField()
    category = models.CharField(max_length=10, blank=True)


class Entity(models.Model):
    campaign = models.ForeignKey(Campaign)

    class Meta:
        verbose_name_plural = 'entities'


class Value(models.Model):
    attribute = models.ForeignKey(Attribute)
    entity = models.ForeignKey(Entity, related_name='values')
