from rest_framework import serializers
from wq.db.rest.serializers import ModelSerializer
from wq.db.patterns.base import serializers as base
from wq.db.rest.models import get_by_identifier, ContentType

from .models import (
    Relationship, InverseRelationship,
    RelationshipType, InverseRelationshipType
)


class ContentTypeField(serializers.SlugRelatedField):
    queryset = ContentType.objects.all()
    slug_field = "model"

    def __init__(self, **kwargs):
        super(serializers.RelatedField, self).__init__(**kwargs)


class RelationshipSerializer(base.TypedAttachmentSerializer):

    def get_fields(self):
        fields = super(RelationshipSerializer, self).get_fields()
        fields['type_label'].source = 'reltype'
        return fields

    def to_representation(self, rel):
        data = super(RelationshipSerializer, self).to_representation(rel)
        data.update(rel.right_dict)
        return data

    def to_internal_value(self, attachment):
        if 'item_id' in attachment and 'type_id' in attachment:
            type = self.Meta.type_model.objects.get(pk=attachment['type_id'])
            cls = type.right.model_class()
            obj = get_by_identifier(cls.objects, attachment['item_id'])
            attachment[self.Meta.item_id_field] = obj.pk
            attachment[self.Meta.item_ct_field] = type.right.pk
            del attachment['item_id']
        return super(RelationshipSerializer, self).to_internal_value(
            attachment
        )

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Relationship

        # patterns-specific
        object_field = 'left'

        # relate-specific
        type_model = RelationshipType
        item_id_field = 'to_object_id'
        item_ct_field = 'to_content_type_id'

        exclude = (
            'from_content_type', 'from_object_id',
        )


class InverseRelationshipSerializer(RelationshipSerializer):
    class Meta(RelationshipSerializer.Meta):
        model = InverseRelationship

        type_model = InverseRelationshipType
        item_id_field = 'from_object_id'
        item_ct_field = 'from_content_type_id'

        exclude = (
            'to_content_type', 'to_object_id'
        )


class RelationshipTypeSerializer(ModelSerializer):
    from_type = ContentTypeField()
    to_type = ContentTypeField()


class RelatedModelSerializer(base.AttachedModelSerializer):
    relationships = RelationshipSerializer(many=True)
    inverserelationships = InverseRelationshipSerializer(many=True)

    def set_parent_object(self, attachment, instance, name):
        if name == "relationships":
            attachment['from_content_object'] = instance
        elif name == "inverserelationships":
            attachment['to_content_object'] = instance
        else:
            super(RelatedModelSerializer, self).set_parent_object(
                attachment, instance, name
            )
