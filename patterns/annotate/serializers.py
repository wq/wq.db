from wq.db.patterns.base import serializers as base
from .models import Annotation


class AnnotationSerializer(base.TypedAttachmentSerializer):
    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Annotation


class AnnotatedModelSerializer(base.AttachedModelSerializer):
    annotations = AnnotationSerializer(many=True)
