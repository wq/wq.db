from django.db import models
from django.contrib.gis.db.models import GeometryField, GeoManager
from django.conf import settings


class RootModel(models.Model):
    slug = models.SlugField()
    description = models.TextField()

    def __str__(self):
        return self.slug


class OneToOneModel(models.Model):
    root = models.OneToOneField(RootModel)

    def __str__(self):
        return "onetoonemodel for %s" % self.root


class ForeignKeyModel(models.Model):
    root = models.ForeignKey(RootModel)

    def __str__(self):
        return "foreignkeymodel for %s" % self.root


class ExtraModel(models.Model):
    root = models.ForeignKey(RootModel, related_name="extramodels")
    alt_root = models.ForeignKey(
        RootModel,
        related_name="extramodel_set",
        null=True,
        blank=True,
    )

    def __str__(self):
        return "extramodel for %s" % self.root


class UserManagedModel(models.Model):
    user = models.ForeignKey("auth.User")


class Parent(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Child(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(Parent)

    def __str__(self):
        return self.name


class ItemType(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=10)
    type = models.ForeignKey(ItemType)

    def __str__(self):
        return self.name


class GeometryModel(models.Model):
    name = models.CharField(max_length=255)
    geometry = GeometryField(srid=settings.SRID)

    objects = GeoManager()

    def __str__(self):
        return self.name


class SlugModel(models.Model):
    code = models.SlugField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class DateModel(models.Model):
    name = models.CharField(max_length=10)
    date = models.DateTimeField()

    def __str__(self):
        return "%s on %s" % (self.name, self.date.date())


class ChoiceModel(models.Model):
    CHOICE_CHOICES = [
        ('one', 'Choice One'),
        ('two', 'Choice Two'),
        ('three', 'Choice Three'),
    ]
    name = models.CharField(max_length=10)
    choice = models.CharField(max_length=10, choices=CHOICE_CHOICES)

    def __str__(self):
        return "%s: %s" % (self.name, self.choice)
