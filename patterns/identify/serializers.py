from rest_framework import serializers
from wq.db.patterns.base.serializers import TypedAttachmentSerializer
from wq.db.rest import app

from .models import Identifier, Authority


class IdentifierSerializer(TypedAttachmentSerializer):
    type_model = Authority
    type_field = 'authority'
    attachment_fields = ['id', 'name', 'slug', 'is_primary']
    required_fields = ['name']

    url = serializers.Field()

    @property
    def expected_types(self):
        return [None] + list(Authority.objects.all())

    def create_dict(self, atype, data, fields, index):
        obj = super(IdentifierSerializer, self).create_dict(
            atype, data, fields, index
        )
        if obj is None:
            return obj
        if 'is_primary' not in obj:
            obj['is_primary'] = (index == 0)
        return obj

    class Meta(TypedAttachmentSerializer.Meta):
        read_only_fields = ('slug',)

app.router.register_serializer(Identifier, IdentifierSerializer)
