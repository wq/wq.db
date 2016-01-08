from wq.db import rest
from wq.db.patterns import rest as patterns
from .models import (
    AnnotatedModel, IdentifiedModel, MarkedModel, LocatedModel,
    RelatedModel, AnotherRelatedModel,
    IdentifiedRelatedModel, IdentifiedMarkedModel,
    NaturalKeyChild, ModelWithNaturalKey,
    CustomPatternModel, CustomTypedPatternModel,
)
from .serializers import (
    CustomPatternSerializer, CustomTypedPatternSerializer,
)
rest.router.register_model(
    AnnotatedModel,
    serializer=patterns.AnnotatedModelSerializer,
)
rest.router.register_model(
    IdentifiedModel,
    serializer=patterns.IdentifiedModelSerializer,
)
rest.router.register_model(
    LocatedModel,
    serializer=patterns.LocatedModelSerializer,
)
rest.router.register_model(
    MarkedModel,
    serializer=patterns.MarkedModelSerializer,
)
rest.router.register_model(
    RelatedModel,
    serializer=patterns.RelatedModelSerializer,
)
rest.router.register_model(
    AnotherRelatedModel,
    serializer=patterns.RelatedModelSerializer,
)
rest.router.register_model(
    IdentifiedRelatedModel,
    serializer=patterns.IdentifiedRelatedModelSerializer,
)
rest.router.register_model(
    IdentifiedMarkedModel,
    serializer=patterns.IdentifiedMarkedModelSerializer,
)
rest.router.register_model(
    NaturalKeyChild,
    serializer=patterns.NaturalKeySerializer,
)
rest.router.register_model(
    ModelWithNaturalKey,
    serializer=patterns.NaturalKeyModelSerializer,
)
rest.router.register_model(
    CustomPatternModel,
    serializer=CustomPatternSerializer,
)
rest.router.register_model(
    CustomTypedPatternModel,
    serializer=CustomTypedPatternSerializer,
)
