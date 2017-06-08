from wq.db import rest
from wq.db.patterns import rest as patterns
from wq.db.patterns.identify.views import IdentifiedModelViewSet
from wq.db.patterns.relate.views import RelatedModelViewSet
from .models import (
    AnnotatedModel, IdentifiedModel, MarkedModel, LocatedModel,
    RelatedModel, AnotherRelatedModel,
    IdentifiedAnnotatedModel,
    IdentifiedRelatedModel, IdentifiedMarkedModel,
    CustomPatternModel, CustomTypedPatternModel, CustomType,
    Campaign, Attribute, Entity
)
from .serializers import (
    CustomPatternSerializer, CustomTypedPatternSerializer,
)
rest.router.register_model(
    AnnotatedModel,
    serializer=patterns.AnnotatedModelSerializer,
    fields='__all__',
)
rest.router.register_model(
    IdentifiedModel,
    serializer=patterns.IdentifiedModelSerializer,
    fields='__all__',
    viewset=IdentifiedModelViewSet,
)
rest.router.register_model(
    LocatedModel,
    serializer=patterns.LocatedModelSerializer,
    fields='__all__',
)
rest.router.register_model(
    MarkedModel,
    serializer=patterns.MarkedModelSerializer,
    fields='__all__',
)
rest.router.register_model(
    RelatedModel,
    serializer=patterns.RelatedModelSerializer,
    fields='__all__',
    viewset=RelatedModelViewSet,
)
rest.router.register_model(
    AnotherRelatedModel,
    serializer=patterns.RelatedModelSerializer,
    fields='__all__',
    viewset=RelatedModelViewSet,
)
rest.router.register_model(
    IdentifiedAnnotatedModel,
    serializer=patterns.IdentifiedAnnotatedModelSerializer,
    fields='__all__',
)
rest.router.register_model(
    IdentifiedRelatedModel,
    serializer=patterns.IdentifiedRelatedModelSerializer,
    fields='__all__',
)
rest.router.register_model(
    IdentifiedMarkedModel,
    serializer=patterns.IdentifiedMarkedModelSerializer,
    fields='__all__',
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
