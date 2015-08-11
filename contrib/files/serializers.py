from rest_framework import serializers
from wq.db.rest.serializers import ModelSerializer
from wq.db.patterns.base import serializers as base
from .models import FileField, FileType
from django.core.files.uploadedfile import UploadedFile


class FileSerializer(ModelSerializer):
    is_image = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        self.serializer_field_mapping[FileField] = serializers.FileField
        super(FileSerializer, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        obj = super(FileSerializer, self).to_internal_value(data)
        if obj and hasattr(obj, 'user') and obj.user is None:
            if 'request' in self.context:
                user = self.context['request'].user
                if user.is_authenticated():
                    obj.user_id = user.pk
        return obj


class FileAttachmentListSerializer(base.TypedAttachmentListSerializer):
    def get_value(self, dictionary):
        values = dictionary.get(self.source, None)
        if not isinstance(values, list):
            values = [values]
        if all(isinstance(value, UploadedFile) for value in values):
            return [
                {'file': value} for value in values
            ]
        return super(FileAttachmentListSerializer, self).get_value(dictionary)


class FileAttachmentSerializer(base.TypedAttachmentSerializer, FileSerializer):
    attachment_fields = ['id', 'name', 'file']
    type_model = FileType

    class Meta(base.TypedAttachmentSerializer.Meta):
        list_serializer_class = FileAttachmentListSerializer


class FileAttachedModelSerializer(base.AttachedModelSerializer):
    pass
