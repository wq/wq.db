from wq.db.rest import app
from wq.db.patterns.base.serializers import TypedAttachmentSerializer
from wq.db.patterns.base import swapper

from wq.db.rest.models import get_ct

Annotation = swapper.load_model('annotate', 'Annotation')
AnnotationType = swapper.load_model('annotate', 'AnnotationType')


class AnnotationSerializer(TypedAttachmentSerializer):
    attachment_fields = ['id', 'value']
    type_model = AnnotationType

    @property
    def expected_types(self):
        ct = get_ct(self.parent.opts.model)
        return AnnotationType.objects.filter(contenttype=ct)

app.router.register_serializer(Annotation, AnnotationSerializer)
