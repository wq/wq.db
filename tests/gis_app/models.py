from django.conf import settings
from wq.db.patterns.models import LabelModel


if settings.WITH_GIS:
    from django.contrib.gis.db import models

    class GeometryModel(LabelModel):
        name = models.CharField(max_length=255)
        geometry = models.GeometryField(srid=settings.SRID)

    class PointModel(LabelModel):
        name = models.CharField(max_length=255)
        geometry = models.PointField(srid=settings.SRID)

else:
    GeometryModel = None
    PointModel = None
