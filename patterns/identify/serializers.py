from rest_framework import serializers
from wq.db.patterns.base import serializers as base
from wq.db.rest.models import get_object_id
from .models import Identifier, Authority


class IdentifierListSerializer(base.TypedAttachmentListSerializer):
    def to_internal_value(self, data):
        data = super(IdentifierListSerializer, self).to_internal_value(data)
        primary = [ident for ident in data if ident.get('is_primary', None)]
        if not any(primary) and len(data) > 0:
            data[0]['is_primary'] = True
        return data


class IdentifierSerializer(base.TypedAttachmentSerializer):
    type_model = Authority
    type_field = 'authority_id'
    attachment_fields = ['id', 'name', 'slug', 'is_primary']
    required_fields = ['name']

    url = serializers.ReadOnlyField()

    @property
    def expected_types(self):
        return [None] + list(Authority.objects.all())

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Identifier
        list_serializer_class = IdentifierListSerializer


class IdentifiedModelSerializer(base.AttachedModelSerializer):
    id = serializers.SerializerMethodField()
    identifiers = IdentifierSerializer(many=True)

    def get_id(self, instance):
        return get_object_id(instance)

    class Meta:
        list_exclude = ('identifiers',)
