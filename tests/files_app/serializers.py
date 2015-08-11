from wq.db.contrib.files.serializers import (
    FileAttachmentSerializer, FileAttachedModelSerializer
)
from .models import Photo


class PhotoSerializer(FileAttachmentSerializer):
    class Meta(FileAttachmentSerializer.Meta):
        model = Photo


class PhotoAttachedModelSerializer(FileAttachedModelSerializer):
    photos = PhotoSerializer(many=True)
