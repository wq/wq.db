from wq.db.patterns.base.serializers import TypedAttachmentSerializer
import swapper

from wq.db.rest.models import get_ct

AnnotationType = swapper.load_model('annotate', 'AnnotationType')


class AnnotationSerializer(TypedAttachmentSerializer):
    attachment_fields = ['id', 'value']
    type_model = AnnotationType

    @property
    def expected_types(self):
        ct = get_ct(self.parent.opts.model)
        return AnnotationType.objects.filter(contenttype=ct)
