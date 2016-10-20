from django.db import models
from django.contrib.gis.db.models import GeometryField, GeoManager
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import pystache


class LabeledModel(models.Model):
    wq_label_template = ""

    def __str__(self):
        return pystache.render(self.wq_label_template, self)

    class Meta:
        abstract = True


class RootModel(LabeledModel):
    slug = models.SlugField()
    description = models.TextField()

    wq_label_template = "{{slug}}"


class OneToOneModel(LabeledModel):
    root = models.OneToOneField(RootModel)

    wq_label_template = "onetoonemodel for {{root}}"


class ForeignKeyModel(LabeledModel):
    root = models.ForeignKey(RootModel)

    wq_label_template = "foreignkeymodel for {{root}}"


class ExtraModel(LabeledModel):
    root = models.ForeignKey(RootModel, related_name="extramodels")
    alt_root = models.ForeignKey(
        RootModel,
        related_name="extramodel_set",
        null=True,
        blank=True,
    )

    wq_label_template = "extramodel for {{root}}"


class UserManagedModel(models.Model):
    user = models.ForeignKey("auth.User")


class Parent(LabeledModel):
    name = models.CharField(max_length=10)

    wq_label_template = "{{name}}"


class Child(LabeledModel):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(Parent, related_name="children")

    wq_label_template = "{{name}}"


class ItemType(LabeledModel):
    name = models.CharField(max_length=10)
    active = models.BooleanField(default=True)

    wq_label_template = "{{name}}"


class Item(LabeledModel):
    name = models.CharField(max_length=10)
    type = models.ForeignKey(ItemType)

    wq_label_template = "{{name}}"


class GeometryModel(LabeledModel):
    name = models.CharField(max_length=255)
    geometry = GeometryField(srid=settings.SRID)

    objects = GeoManager()

    wq_label_template = "{{name}}"


class SlugModel(LabeledModel):
    code = models.SlugField()
    name = models.CharField(max_length=255)

    wq_label_template = "{{name}}"


class SlugRefParent(LabeledModel):
    ref = models.ForeignKey(SlugModel)
    name = models.CharField(max_length=255)

    wq_label_template = "{{name}}{{#ref_id}} ({{ref}}){{/ref_id}}"


class SlugRefChild(models.Model):
    parent = models.ForeignKey(SlugRefParent)
    name = models.CharField(max_length=255)


class DateModel(models.Model):
    name = models.CharField(max_length=10)
    date = models.DateTimeField()
    empty_date = models.DateTimeField(null=True)

    def __str__(self):
        return "%s on %s" % (self.name, self.date.date())


class ChoiceModel(LabeledModel):
    CHOICE_CHOICES = [
        ('one', 'Choice One'),
        ('two', 'Choice Two'),
        ('three', 'Choice Three'),
    ]
    name = models.CharField(
        max_length=10,
        help_text='Enter Name',
    )
    choice = models.CharField(
        max_length=10,
        help_text='Pick One',
        choices=CHOICE_CHOICES,
    )

    wq_label_template = "{{name}}: {{choice}}"


class TranslatedModel(models.Model):
    name = models.CharField(
        verbose_name=_('translated model name'),
        max_length=255,
    )
