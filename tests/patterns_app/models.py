from wq.db.patterns import models
from django.contrib.gis.db.models import GeometryField, GeoManager
from django.conf import settings


class AnnotatedModel(models.AnnotatedModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class IdentifiedModel(models.IdentifiedModel):
    name = models.CharField(max_length=255)


class IdentifiedAnnotatedModel(models.IdentifiedModel, models.AnnotatedModel):
    name = models.CharField(max_length=255)


class MarkedModel(models.MarkedModel):
    name = models.CharField(max_length=255)


class LocatedModel(models.LocatedModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class GeometryModel(models.Model):
    name = models.CharField(max_length=255)
    geometry = GeometryField(srid=settings.SRID)

    objects = GeoManager()

    def __unicode__(self):
        return self.name
