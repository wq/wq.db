from wq.db import rest
from .models import Location
from .serializers import LocationSerializer

rest.router.register_model(Location, serializer=LocationSerializer)
