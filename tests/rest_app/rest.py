from wq.db import rest
from .models import (
    RootModel, UserManagedModel, Parent, Child, ItemType, Item,
    GeometryModel, PointModel, FileModel, ImageModel,
    SlugModel, SlugRefParent, SlugRefChild,
    DateModel, ChoiceModel, TranslatedModel,
)
from .serializers import (
    RootModelSerializer, ParentSerializer, ItemSerializer,
    SlugRefChildSerializer,
)

rest.router.register_model(
    RootModel,
    url="",
    lookup="slug",
    serializer=RootModelSerializer,
    fields="__all__",
)
rest.router.register_model(
    UserManagedModel,
    fields="__all__",
)
rest.router.register_model(
    Parent,
    serializer=ParentSerializer,
    fields="__all__",
)
rest.router.register_model(
    Child,
    per_page=100,
    url="children",
    fields="__all__",
)
rest.router.register_model(
    ItemType,
    fields="__all__",
)
rest.router.register_model(
    Item,
    serializer=ItemSerializer,
    fields="__all__",
)
rest.router.register_model(
    GeometryModel,
    fields="__all__",
)
rest.router.register_model(
    PointModel,
    fields="__all__",
)
rest.router.register_model(
    FileModel,
    fields="__all__",
)
rest.router.register_model(
    ImageModel,
    fields="__all__",
)
rest.router.register_model(
    SlugModel,
    lookup="code",
    fields="__all__",
)
rest.router.register_model(
    SlugRefParent,
    fields="__all__",
)
rest.router.register_model(
    SlugRefChild,
    url="slugrefchildren",
    serializer=SlugRefChildSerializer,
    fields="__all__",
)
rest.router.register_model(
    DateModel,
    fields="__all__",
)
rest.router.register_model(
    ChoiceModel,
    fields="__all__",
)
rest.router.register_model(
    TranslatedModel,
    fields="__all__",
)
rest.router.set_extra_config(debug=True)

rest.router.add_page("rest_context", {})
rest.router.add_page("auth_context", {})
