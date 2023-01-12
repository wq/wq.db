from django.conf import settings
from wq.db.rest.models import LabelModel


if settings.WITH_GIS:
    from django.contrib.gis.db import models

    class GeometryModel(LabelModel):
        name = models.CharField(max_length=255)
        geometry = models.GeometryField(srid=4326)

    class PointModel(LabelModel):
        name = models.CharField(max_length=255)
        geometry = models.PointField(srid=4326)

else:
    GeometryModel = None
    PointModel = None
