from wq.db import resources
from wq.db.util import get_id, geturlbase

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
        return map(serialize_relationship, instance.relationships.all())

class InverseRelationshipContextMixin(RelationshipContextMixin):
    model = InverseRelationship
    name  = 'inverserelationships'
    def get_data(self, instance):
        return map(serialize_relationship, instance.inverse_relationships.all())

def serialize_relationship(rel, include_pointer=False):
    data = {
        'id':    rel.pk,
        'type':  unicode(rel.reltype),
        'label': unicode(rel.right),
        'id':    rel.right.pk,
        'url':   '%s/%s' % (geturlbase(rel.reltype.right), rel.right.pk)
    }
    if include_pointer:
        idname = get_id(rel.reltype.left) + '_id'
        data[idname] = rel.left.pk
    return data

resources.register(Relationship, RelationshipResource)
resources.register(InverseRelationship, InverseRelationshipResource)
resources.register_context_mixin(RelationshipContextMixin)
resources.register_context_mixin(InverseRelationshipContextMixin)
