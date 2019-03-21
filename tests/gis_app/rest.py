from wq.db import rest
from .models import GeometryModel, PointModel
from django.conf import settings

if settings.WITH_GIS:
    rest.router.register_model(
        GeometryModel,
        fields="__all__",
    )
    rest.router.register_model(
        PointModel,
        fields="__all__",
    )
