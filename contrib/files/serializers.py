from rest_framework.serializers import FileField as RestFileField, Field
from wq.db.rest import serializers
from wq.db.rest import app
from .models import FileField, File


class FileSerializer(serializers.ModelSerializer):
    is_image = Field('is_image')

    def __init__(self, *args, **kwargs):
        self.field_mapping[FileField] = RestFileField
        super(FileSerializer, self).__init__(*args, **kwargs)

    def from_native(self, data, files):
        obj = super(FileSerializer, self).from_native(data, files)
        if 'request' in self.context and obj and obj.user is None:
            user = self.context['request'].user
            if user.is_authenticated():
                obj.user = user
        return obj

app.router.register_serializer(File, FileSerializer)
