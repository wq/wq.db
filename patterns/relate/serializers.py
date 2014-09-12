from wq.db.rest.serializers import ModelSerializer, ContentTypeField
from wq.db.patterns.base.serializers import TypedAttachmentSerializer
from wq.db.rest.models import get_ct, get_object_id, get_by_identifier

from .models import (
    Relationship, InverseRelationship,
    RelationshipType, InverseRelationshipType
)


class RelationshipSerializer(TypedAttachmentSerializer):
    attachment_fields = ['id', 'item_id']
    required_fields = ['item_id']
    type_model = RelationshipType
    object_field = 'left'
    item_id_field = 'to_object_id'
    parent_id_field = 'from_object_id'

    def get_default_fields(self):
        fields = super(RelationshipSerializer, self).get_default_fields()
        del fields[self.parent_id_field]
        fields['type_label'].source = 'reltype'
        return fields

    def to_native(self, rel):
        data = super(RelationshipSerializer, self).to_native(rel)
        del data[self.item_id_field]
        data.update(rel.right_dict)
        return data

    def create_dict(self, atype, data, fields, index):
        attachment = super(RelationshipSerializer, self).create_dict(
            atype, data, fields, index
        )
        if attachment is None:
            return None
        if 'item_id' in attachment and 'type' in attachment:
            type = self.type_model.objects.get(pk=attachment['type'])
            cls = type.right.model_class()
            obj = get_by_identifier(cls.objects, attachment['item_id'])
            attachment[self.item_id_field] = obj.pk
            del attachment['item_id']
        return attachment


class InverseRelationshipSerializer(RelationshipSerializer):
    item_id_field = 'from_object_id'
    parent_id_field = 'to_object_id'
    type_model = InverseRelationshipType

    def get_default_fields(self):
        fields = super(
            InverseRelationshipSerializer, self
        ).get_default_fields()
        return fields


class RelationshipTypeSerializer(ModelSerializer):
    from_type = ContentTypeField()
    to_type = ContentTypeField()

    class Meta:
        exclude = ('for',)
