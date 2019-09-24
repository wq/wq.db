from wq.db import rest
from .models import (
    RootModel, UserManagedModel, Parent, Child, ItemType, Item,
    FileModel, ImageModel,
    SlugModel, SlugRefParent, SlugRefChild,
    DateModel, ChoiceModel, TranslatedModel,
    CharFieldModel, ExpensiveModel
)
from .serializers import (
    RootModelSerializer, ParentSerializer, ItemSerializer,
    SlugRefChildSerializer, ExpensiveSerializer,
)


def cache_users_own_data(qs, req):
    if req.user.is_authenticated:
        return qs.filter(user=req.user)
    else:
        return qs.none()


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
    cache_filter=cache_users_own_data,
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
    cache="all",
)
rest.router.register_model(
    Item,
    serializer=ItemSerializer,
    fields="__all__",
    cache="none",
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
rest.router.register_model(
    CharFieldModel,
    fields="__all__",
)
rest.router.register_model(
    ExpensiveModel,
    serializer=ExpensiveSerializer,
    queryset=ExpensiveModel.objects.defer('expensive', 'more_expensive'),
)

rest.router.add_page("rest_context", {})
rest.router.add_page("auth_context", {})
rest.router.add_page("script_context", {})
