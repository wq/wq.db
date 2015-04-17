from wq.db import rest
from .serializers import AnnotationSerializer
from .models import Annotation, AnnotationType

rest.router.register_model(Annotation, serializer=AnnotationSerializer)
rest.router.register_model(AnnotationType)
