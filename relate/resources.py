from wq.db import resources
from wq.db.util import get_id, geturlbase, get_object_id

from .models import Relationship, InverseRelationship, RelatedModel

class RelationshipResource(resources.ModelResource):
    model = Relationship
    def serialize_model(self, instance):
        return serialize_relationship(instance, True)

class InverseRelationshipResource(RelationshipResource):
    model = InverseRelationship

class RelationshipContextMixin(resources.ContextMixin):
    model = Relationship
    target_model = RelatedModel
    def get_data(self, instance):
        return self.get_groups(instance.relationships.all())

    def get_groups(self, rels):
        groups = {}
        for rel in rels:
            rel = serialize_relationship(rel)
            if rel['type'] not in groups:
                groups[rel['type']] = []
            groups[rel['type']].append(rel)
            del rel['type']

        return [
            {
                'type': key,
                'list': val
            } for key, val in groups.items()
        ]

class InverseRelationshipContextMixin(RelationshipContextMixin):
    model = InverseRelationship
    name  = 'inverserelationships'
    def get_data(self, instance):
        return self.get_groups(instance.inverse_relationships.all())

def serialize_relationship(rel, include_pointer=False):
    oid = get_object_id(rel.right)
    data = {
        'id':    rel.pk,
        'type':  unicode(rel.reltype),
        'label': unicode(rel.right),
        'id':    oid,
        'url':   '%s/%s' % (geturlbase(rel.reltype.right), oid)
    }
    if include_pointer:
        idname = get_id(rel.reltype.left) + '_id'
        data[idname] = get_object_id(rel.left)
    return data

resources.register(Relationship, RelationshipResource)
resources.register(InverseRelationship, InverseRelationshipResource)
resources.register_context_mixin(RelationshipContextMixin)
resources.register_context_mixin(InverseRelationshipContextMixin)
