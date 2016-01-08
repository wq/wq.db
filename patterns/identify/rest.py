from wq.db import rest
from .models import Authority


rest.router.register_model(Authority)
