from wq.db import rest
from .models import NaturalKeyParent, ModelWithNaturalKey


rest.router.register(NaturalKeyParent, fields="__all__")
rest.router.register(ModelWithNaturalKey, fields="__all__")
