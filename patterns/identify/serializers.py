from wq.db.rest.serializers import ModelSerializer
from wq.db.rest import app
from wq.db.rest.models import get_ct, get_object_id

from .models import Identifier

class IdentifierSerializer(ModelSerializer):

    def to_native(self, ident):
        data = {
            'id':         ident.pk,
            'name':       ident.name,
            'authority':  getattr(ident.authority, 'name', None),
            'url':        ident.url,
            'is_primary': ident.is_primary
        }

        has_parent = self.parent and hasattr(self.parent.opts, 'model')
        if has_parent:
            pass
        else:
            # Include pointer to parent object (see annotate/serializers.py)
            idname = get_ct(ident.content_object).identifier + '_id'
            data[idname] = get_object_id(ident.content_object)

        return data

app.router.register_serializer(Identifier, IdentifierSerializer)
