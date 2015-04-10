from wq.db.rest import app
from .models import (
    RootModel, UserManagedModel, Parent, Child, ItemType, Item, GeometryModel,
    SlugModel,
)
from .serializers import RootModelSerializer

app.router.register_model(
    RootModel,
    url="",
    lookup="slug",
    serializer=RootModelSerializer,
)
app.router.register_model(UserManagedModel)
app.router.register_model(Parent)
app.router.register_model(Child, per_page=100)
app.router.register_model(ItemType)
app.router.register_model(Item)
app.router.register_model(GeometryModel)
app.router.register_model(SlugModel, lookup="code")
app.router.set_extra_config(debug=True)

app.router.add_page("rest_context", {})
app.router.add_page("auth_context", {})
