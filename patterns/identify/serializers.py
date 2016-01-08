from rest_framework import serializers
from wq.db.patterns.base import serializers as base
from wq.db.rest.models import get_object_id
from .models import Identifier, Authority


class IdentifierListSerializer(base.TypedAttachmentListSerializer):
    def to_internal_value(self, data):
        data = super(IdentifierListSerializer, self).to_internal_value(data)
        primary = [
            ident for ident in data
            if ident and ident.get('is_primary', None)
        ]
        if not any(primary) and len(data) > 0:
            for ident in data:
                if ident:
                    ident['is_primary'] = True
                    break
        return data


class IdentifierSerializer(base.TypedAttachmentSerializer):
    url = serializers.ReadOnlyField()

    @property
    def expected_types(self):
        return [None] + list(Authority.objects.all())

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Identifier
        list_serializer_class = IdentifierListSerializer

        # patterns-specific
        type_field = 'authority_id'


class IdentifiedModelSerializer(base.AttachedModelSerializer):
    id = serializers.SerializerMethodField()
    identifiers = IdentifierSerializer(many=True)

    def get_id(self, instance):
        return get_object_id(instance)
