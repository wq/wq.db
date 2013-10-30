from wq.db.rest import app
from .models import Identifier, Authority
from .serializers import IdentifierSerializer

app.router.register_model(Identifier, serializer=IdentifierSerializer)
app.router.register_model(Authority)
