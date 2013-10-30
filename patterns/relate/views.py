from wq.db.rest import app
from .models import Relationship, InverseRelationship, RelationshipType
from .serializers import (
    RelationshipSerializer,
    InverseRelationshipSerializer,
    RelationshipTypeSerializer
)

app.router.register_model(
    Relationship, serializer=RelationshipSerializer
)
app.router.register_model(
    InverseRelationship, serializer=InverseRelationshipSerializer
)
app.router.register_model(
    RelationshipType, serializer=RelationshipTypeSerializer
)
