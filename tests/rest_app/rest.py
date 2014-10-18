from wq.db.rest import app
from .models import RootModel, UserManagedModel, Parent, Child
app.router.register_model(RootModel, url="")
app.router.register_model(UserManagedModel)
app.router.register_model(Parent)
app.router.register_model(Child)
app.router.set_extra_config(debug=True)
