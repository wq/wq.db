from wq.db.patterns.file.serializers import (
    FileSerializer, FiledModelSerializer
)
from .models import Photo


class PhotoSerializer(FileSerializer):
    class Meta(FileSerializer.Meta):
        model = Photo


class PhotoAttachedModelSerializer(FiledModelSerializer):
    files = PhotoSerializer(many=True)
