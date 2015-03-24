from wq.db.rest import app
from wq.db.patterns import rest as patterns
from .models import (
    AnnotatedModel, IdentifiedModel, MarkedModel, LocatedModel,
    RelatedModel, AnotherRelatedModel,
    IdentifiedRelatedModel, IdentifiedMarkedModel,
)
app.router.register_model(
    AnnotatedModel,
    serializer=patterns.AnnotatedModelSerializer,
)
app.router.register_model(
    IdentifiedModel,
    serializer=patterns.IdentifiedModelSerializer,
)
app.router.register_model(
    LocatedModel,
    serializer=patterns.LocatedModelSerializer,
)
app.router.register_model(
    MarkedModel,
    serializer=patterns.MarkedModelSerializer,
)
app.router.register_model(
    RelatedModel,
    serializer=patterns.RelatedModelSerializer,
)
app.router.register_model(
    AnotherRelatedModel,
    serializer=patterns.RelatedModelSerializer,
)
app.router.register_model(
    IdentifiedRelatedModel,
    serializer=patterns.IdentifiedRelatedModelSerializer,
)
app.router.register_model(
    IdentifiedMarkedModel,
    serializer=patterns.IdentifiedMarkedModelSerializer,
)
