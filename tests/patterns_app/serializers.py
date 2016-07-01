from wq.db.patterns import serializers as patterns

from .models import CustomAttachment, CustomTypedAttachment


class CustomAttachmentSerializer(patterns.AttachmentSerializer):
    class Meta(patterns.AttachmentSerializer.Meta):
        model = CustomAttachment
        exclude = ['parent']

        object_field = 'parent'


class CustomPatternSerializer(patterns.AttachedModelSerializer):
    attachments = CustomAttachmentSerializer(many=True)


class CustomTypedAttachmentSerializer(patterns.TypedAttachmentSerializer):
    class Meta(patterns.TypedAttachmentSerializer.Meta):
        model = CustomTypedAttachment
        exclude = ['parent']

        object_field = 'parent'


class CustomTypedPatternSerializer(patterns.AttachedModelSerializer):
    attachments = CustomTypedAttachmentSerializer(many=True)
