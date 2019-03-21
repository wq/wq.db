from django.db import models
from wq.db.patterns import models as patterns


class IdentifiedModel(patterns.IdentifiedModel):
    pass


class FilterableModel(patterns.LabelModel):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(
        IdentifiedModel, models.CASCADE
    )


class CustomPatternModel(models.Model):
    name = models.CharField(max_length=10)


class CustomAttachment(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(
        CustomPatternModel, models.CASCADE, related_name='attachments',
    )


class CustomTypedPatternModel(models.Model):
    name = models.CharField(max_length=10)


class CustomType(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class CustomTypedAttachment(models.Model):
    name = models.CharField(max_length=10, null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    type = models.ForeignKey(CustomType, models.CASCADE)
    parent = models.ForeignKey(
        CustomTypedPatternModel,
        models.CASCADE,
        related_name='attachments'
    )


class Campaign(models.Model):
    pass


class Attribute(models.Model):
    name = models.CharField(max_length=10)
    campaign = models.ForeignKey(Campaign, models.CASCADE)
    is_active = models.BooleanField()
    category = models.CharField(max_length=10, blank=True)


class Entity(models.Model):
    campaign = models.ForeignKey(Campaign, models.CASCADE)

    class Meta:
        verbose_name_plural = 'entities'


class Value(models.Model):
    attribute = models.ForeignKey(Attribute, models.CASCADE)
    entity = models.ForeignKey(Entity, models.CASCADE, related_name='values')
