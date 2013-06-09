from rest_framework.serializers import FileField as RestFileField, Field
from wq.db.rest import serializers
from wq.db.rest import app
from .models import FileField, File

class FileSerializer(serializers.ModelSerializer):
    is_image = Field('is_image')

    def __init__(self, *args, **kwargs):
        self.field_mapping[FileField] = RestFileField
        super(FileSerializer, self).__init__(*args, **kwargs)

app.router.register_serializer(File, FileSerializer)
