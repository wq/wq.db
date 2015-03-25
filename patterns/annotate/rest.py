from wq.db.rest import app
from .serializers import AnnotationSerializer
from .models import Annotation, AnnotationType

app.router.register_model(Annotation, serializer=AnnotationSerializer)
app.router.register_model(AnnotationType)
