from rest_framework import serializers
from wq.db.patterns.base import serializers as base
from .models import File, FileField
from django.core.files.uploadedfile import UploadedFile


class FileListSerializer(base.TypedAttachmentListSerializer):
    def get_value(self, dictionary):
        values = dictionary.get(self.source, None)
        if not isinstance(values, list):
            values = [values]
        if all(isinstance(value, UploadedFile) for value in values):
            return [
                {'file': value} for value in values
            ]
        return super(FileListSerializer, self).get_value(dictionary)


class FileSerializer(base.TypedAttachmentSerializer):
    is_image = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        self.serializer_field_mapping[FileField] = serializers.FileField
        super(FileSerializer, self).__init__(*args, **kwargs)

    class Meta(base.TypedAttachmentSerializer.Meta):
        list_serializer_class = FileListSerializer
        model = File
        wq_config = {
            'initial': None,
        }


class FiledModelSerializer(base.AttachedModelSerializer):
    files = FileSerializer(many=True)
