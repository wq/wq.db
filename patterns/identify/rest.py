from wq.db import rest
from .models import Identifier, Authority
from .serializers import IdentifierSerializer

rest.router.register_model(Identifier, serializer=IdentifierSerializer)
rest.router.register_model(Authority)
