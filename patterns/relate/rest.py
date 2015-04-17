from wq.db import rest
from .models import Relationship, InverseRelationship, RelationshipType
from .serializers import (
    RelationshipSerializer,
    InverseRelationshipSerializer,
    RelationshipTypeSerializer
)

rest.router.register_model(
    Relationship, serializer=RelationshipSerializer
)
rest.router.register_model(
    InverseRelationship, serializer=InverseRelationshipSerializer
)
rest.router.register_model(
    RelationshipType, serializer=RelationshipTypeSerializer
)
