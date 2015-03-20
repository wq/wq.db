from rest_framework import serializers
from wq.db.rest.serializers import ModelSerializer
from .models import FileField


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
