from wq.db import rest
from .models import AnnotationType


rest.router.register_model(AnnotationType)
