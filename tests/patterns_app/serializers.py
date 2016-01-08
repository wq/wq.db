from wq.db.patterns.base import serializers as base

from .models import CustomAttachment, CustomTypedAttachment


class CustomAttachmentSerializer(base.AttachmentSerializer):
    class Meta(base.AttachmentSerializer.Meta):
        model = CustomAttachment
        exclude = ['parent']

        object_field = 'parent'


class CustomPatternSerializer(base.AttachedModelSerializer):
    attachments = CustomAttachmentSerializer(many=True)


class CustomTypedAttachmentSerializer(base.TypedAttachmentSerializer):
    class Meta(base.TypedAttachmentSerializer.Meta):
        model = CustomTypedAttachment
        exclude = ['parent']

        object_field = 'parent'


class CustomTypedPatternSerializer(base.AttachedModelSerializer):
    attachments = CustomTypedAttachmentSerializer(many=True)
