from wq.db.patterns import models
from django.contrib.gis.db.models import GeometryField, GeoManager
from django.conf import settings


class RootModel(models.IdentifiedModel):
    description = models.TextField()


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


class Child(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(Parent)


class ItemType(models.Model):
    name = models.CharField(max_length=10)


class Item(models.Model):
    name = models.CharField(max_length=10)
    type = models.ForeignKey(ItemType)


class GeometryModel(models.Model):
    name = models.CharField(max_length=255)
    geometry = GeometryField(srid=settings.SRID)

    objects = GeoManager()

    def __str__(self):
        return self.name
