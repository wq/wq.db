from wq.db import rest
from wq.db.patterns import rest as patterns
from wq.db.patterns.identify.views import IdentifiedModelViewSet
from .models import (
    IdentifiedModel,
    CustomPatternModel, CustomTypedPatternModel, CustomType,
    Campaign, Attribute, Entity
)
from .serializers import (
    CustomPatternSerializer, CustomTypedPatternSerializer,
)
rest.router.register_model(
    IdentifiedModel,
    serializer=patterns.IdentifiedModelSerializer,
    fields='__all__',
    viewset=IdentifiedModelViewSet,
)
rest.router.register_model(
    CustomPatternModel,
    serializer=CustomPatternSerializer,
    fields='__all__',
)
rest.router.register_model(
    CustomTypedPatternModel,
    serializer=CustomTypedPatternSerializer,
    fields='__all__',
)
rest.router.register_model(
    CustomType,
    fields='__all__',
)
rest.router.register_model(
    Campaign,
    fields='__all__')
rest.router.register_model(
    Attribute,
    fields='__all__')
rest.router.register_model(
    Entity,
    fields='__all__')
