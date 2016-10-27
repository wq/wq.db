from wq.db import rest
from .models import RelationshipType
from .serializers import RelationshipTypeSerializer


rest.router.register_model(
    RelationshipType,
    serializer=RelationshipTypeSerializer,
    fields="__all__",
)
