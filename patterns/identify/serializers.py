from rest_framework import serializers
from wq.db.patterns.base import serializers as base
from wq.db.rest.serializers import ModelSerializer
from wq.db.rest.models import get_object_id
from .models import Identifier, Authority


class IdentifierSerializer(base.TypedAttachmentSerializer):
    type_model = Authority
    type_field = 'authority_id'
    attachment_fields = ['id', 'name', 'slug', 'is_primary']
    required_fields = ['name']

    url = serializers.ReadOnlyField()

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

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Identifier


class IdentifiedModelSerializer(base.AttachedModelSerializer):
    id = serializers.SerializerMethodField()
    identifiers = IdentifierSerializer(many=True)

    def get_id(self, instance):
        return get_object_id(instance)

    class Meta:
        list_exclude = ('identifiers',)
