from wq.db.rest.serializers import ModelSerializer, ContentTypeField
from wq.db.patterns.base import serializers as base
from wq.db.rest.models import get_by_identifier

from .models import (
    Relationship, InverseRelationship,
    RelationshipType, InverseRelationshipType
)


class RelationshipSerializer(base.TypedAttachmentSerializer):
    attachment_fields = ['id', 'item_id']
    required_fields = ['item_id']
    type_model = RelationshipType
    object_field = 'left'
    item_id_field = 'to_object_id'
    item_ct_field = 'to_content_type_id'
    parent_id_field = 'from_object_id'

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
            type = self.type_model.objects.get(pk=attachment['type_id'])
            cls = type.right.model_class()
            obj = get_by_identifier(cls.objects, attachment['item_id'])
            attachment[self.item_id_field] = obj.pk
            attachment[self.item_ct_field] = type.right.pk
            del attachment['item_id']
        return super(RelationshipSerializer, self).to_internal_value(
            attachment
        )

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Relationship
        exclude = (
            'from_content_type', 'from_object_id',
        )


class InverseRelationshipSerializer(RelationshipSerializer):
    item_id_field = 'from_object_id'
    item_ct_field = 'from_content_type_id'
    parent_id_field = 'to_object_id'
    type_model = InverseRelationshipType

    class Meta(RelationshipSerializer.Meta):
        model = InverseRelationship
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

    class Meta:
        list_exclude = ('relationships', 'inverserelationships')
