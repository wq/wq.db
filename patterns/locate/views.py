from wq.db.rest import app
from .models import Location
from .serializers import LocationSerializer

app.router.register_model(Location, serializer=LocationSerializer)
