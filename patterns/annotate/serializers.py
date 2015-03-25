from wq.db.patterns.base import serializers as base
from .models import AnnotationType, Annotation


class AnnotationSerializer(base.TypedAttachmentSerializer):
    attachment_fields = ['id', 'value']
    type_model = AnnotationType

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Annotation


class AnnotatedModelSerializer(base.AttachedModelSerializer):
    annotations = AnnotationSerializer(many=True)

    class Meta:
        list_exclude = ('annotations',)
