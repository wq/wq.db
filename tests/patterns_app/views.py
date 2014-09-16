from wq.db.rest import app
from .models import AnnotatedModel, MarkedModel, LocatedModel, GeometryModel
app.router.register_model(AnnotatedModel)
app.router.register_model(LocatedModel)
app.router.register_model(MarkedModel)
app.router.register_model(GeometryModel)
