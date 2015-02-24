from wq.db.rest import app
from .models import (
    AnnotatedModel, IdentifiedModel, MarkedModel, LocatedModel,
    RelatedModel, AnotherRelatedModel
)
app.router.register_model(AnnotatedModel)
app.router.register_model(IdentifiedModel)
app.router.register_model(LocatedModel)
app.router.register_model(MarkedModel)
app.router.register_model(RelatedModel)
app.router.register_model(AnotherRelatedModel)
