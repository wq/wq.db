from wq.db import rest
from .models import GeometryModel, PointModel
from django.conf import settings

if settings.WITH_GIS:
    rest.router.register(GeometryModel, fields="__all__")
    rest.router.register(PointModel, fields="__all__", defer_geometry=True)
