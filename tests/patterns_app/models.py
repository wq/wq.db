from django.db import models
from wq.db.rest.models import LabelModel


class Campaign(LabelModel):
    slug = models.SlugField()
    name = models.CharField(max_length=10)


class Attribute(LabelModel):
    name = models.CharField(max_length=10)
    campaign = models.ForeignKey(
        Campaign, models.CASCADE, related_name="attributes"
    )
    is_active = models.BooleanField(default=True)


class Entity(LabelModel):
    name = models.CharField(max_length=10)
    campaign = models.ForeignKey(Campaign, models.CASCADE)

    class Meta:
        verbose_name_plural = "entities"


class Value(models.Model):
    attribute = models.ForeignKey(Attribute, models.CASCADE)
    entity = models.ForeignKey(Entity, models.CASCADE, related_name="values")
    value = models.TextField()
