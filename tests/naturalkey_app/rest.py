from wq.db import rest
from .models import (
    NaturalKeyParent,
    ModelWithNaturalKey
)
from wq.db.patterns.serializers import NaturalKeyModelSerializer


rest.router.register_model(
    NaturalKeyParent,
    fields="__all__",
)
rest.router.register_model(
    ModelWithNaturalKey,
    serializer=NaturalKeyModelSerializer,
    fields="__all__",
)
