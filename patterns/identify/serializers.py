from rest_framework import serializers
from wq.db.patterns.base.serializers import TypedAttachmentSerializer
from wq.db.rest import app

from .models import Identifier, Authority

class IdentifierSerializer(TypedAttachmentSerializer):
    type_model = Authority
    type_field = 'authority'
    value_field = 'name'

    url = serializers.Field()

    @property
    def expected_types(self):
        return [None] + list(Authority.objects.all())

    def create_dict(self, atype, val, existing, index):
        obj = super(IdentifierSerializer, self).create_dict(atype, val, existing, index)
        if existing:
            obj['is_primary'] = existing.is_primary
        else:
            obj['is_primary'] = (index == 0)
        return obj

    class Meta(TypedAttachmentSerializer.Meta):
        exclude = TypedAttachmentSerializer.Meta.exclude + ('valid_from', 'valid_to')
        read_only_fields = ('slug',)

app.router.register_serializer(Identifier, IdentifierSerializer)
