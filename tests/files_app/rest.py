from wq.db import rest
from .serializers import PhotoAttachedModelSerializer
from .models import PhotoAttachedModel

rest.router.register_model(
    PhotoAttachedModel,
    serializer=PhotoAttachedModelSerializer,
    fields="__all__",
)
