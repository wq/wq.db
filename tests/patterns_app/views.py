from wq.db.rest import app
from .models import AnnotatedModel
app.router.register_model(AnnotatedModel)
