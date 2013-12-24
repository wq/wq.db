from wq.db.rest import app
from .models import RootModel, AnnotatedModel
app.router.register_model(RootModel, url="")
app.router.register_model(AnnotatedModel)
