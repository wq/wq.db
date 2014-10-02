from wq.db.rest import app
from .models import RootModel
app.router.register_model(RootModel, url="")
