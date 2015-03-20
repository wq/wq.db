from wq.db.patterns.base import serializers as base
import swapper

from wq.db.rest.models import get_ct

AnnotationType = swapper.load_model(
    'annotate', 'AnnotationType', required=False
)
Annotation = swapper.load_model(
    'annotate', 'Annotation', required=False
)


class AnnotationSerializer(base.TypedAttachmentSerializer):
    attachment_fields = ['id', 'value']
    type_model = AnnotationType

    @property
    def expected_types(self):
        ct = get_ct(self.parent.parent.Meta.model)
        return AnnotationType.objects.filter(contenttype=ct)

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Annotation


class AnnotatedModelSerializer(base.AttachedModelSerializer):
    annotations = AnnotationSerializer(many=True)

    class Meta:
        list_exclude = ('annotations',)
