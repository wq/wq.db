from wq.db.rest.serializers import ModelSerializer, ContentTypeField
from wq.db.patterns.base.serializers import TypedAttachmentSerializer
from wq.db.rest import app
from wq.db.rest.models import get_ct, get_object_id, get_by_identifier

from .models import (
    Relationship, InverseRelationship,
    RelationshipType, InverseRelationshipType
)


class RelationshipSerializer(TypedAttachmentSerializer):
    attachment_fields = ['id', 'item_id']
    type_model = RelationshipType
    object_field = 'left'
    item_id_field = 'to_object_id'
    parent_id_field = 'from_object_id'

    def get_default_fields(self):
        fields = super(RelationshipSerializer, self).get_default_fields()
        del fields[self.parent_id_field]
        return fields

    def to_native(self, rel):
        data = super(RelationshipSerializer, self).to_native(rel)
        del data[self.item_id_field]
        oid = get_object_id(rel.right)
        ct = get_ct(rel.right)
        data.update({
            'item_label': unicode(rel.right),
            'item_url': '%s/%s' % (ct.urlbase, oid),
            'item_page': ct.identifier,
            'item_id': oid
        })
        return data

    def create_dict(self, atype, data, fields, index):
        attachment = super(RelationshipSerializer, self).create_dict(
            atype, data, fields, index
        )
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
        fields['type_label'].source = 'reltype'
        return fields


class RelationshipTypeSerializer(ModelSerializer):
    from_type = ContentTypeField()
    to_type = ContentTypeField()

    class Meta:
        exclude = ('for',)

app.router.register_serializer(Relationship, RelationshipSerializer)
app.router.register_serializer(
    InverseRelationship, InverseRelationshipSerializer
)
app.router.register_serializer(RelationshipType, RelationshipTypeSerializer)
