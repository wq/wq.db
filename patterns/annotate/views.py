from wq.db.rest import app
from wq.db.patterns.base import swapper
from .serializers import AnnotationSerializer

Annotation = swapper.load_model('annotate', 'Annotation')
AnnotationType = swapper.load_model('annotate', 'AnnotationType')
app.router.register_model(Annotation, serializer=AnnotationSerializer)
app.router.register_model(AnnotationType)
