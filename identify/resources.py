from wq.db import resources
from wq.db.util import get_id

from .models import Identifier, IdentifiedModel

class IdentifierResource(resources.ModelResource):
    model = Identifier
    def serialize_model(self, instance):
        return serialize_identifier(instance, True)

class IdentifierContextMixin(resources.ContextMixin):
    model = Identifier
    target_model = IdentifiedModel
    def get_data(self, instance):
        return map(serialize_identifier, instance.identifiers.all())

def serialize_identifier(ident, include_pointer=False):
    data = {
        'id':         ident.pk,
        'name':       ident.name,
        'authority':  getattr(ident.authority, 'name', None),
        'url':        ident.url,
        'is_primary': ident.is_primary
    }
    if include_pointer:
        idname = get_id(ident.content_type) + '_id'
        data[idname] = ident.object_id
    return data

resources.register(Identifier, IdentifierResource)
resources.register_context_mixin(IdentifierContextMixin)
