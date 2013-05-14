from wq.db.rest.serializers import ModelSerializer
from wq.db.rest import app
from wq.db.rest.models import get_ct, get_object_id

from .models import Relationship, InverseRelationship

class RelationshipSerializer(ModelSerializer):

    def to_native(self, rel):
        oid = get_object_id(rel.right)
        ct = get_ct(rel.right)
        data = {
            'id':    rel.pk,
            'type':  unicode(rel.reltype),
            'label': unicode(rel.right),
            'id':    oid,
            'url':   '%s/%s' % (ct.urlbase, oid)
        }

        has_parent = self.parent and hasattr(self.parent.opts, 'model')
        if has_parent:
            pass
        else:
            # Include pointer to parent object (see annotate/serializers.py)
            idname = get_ct(rel.left).identifier + '_id'
            data[idname] = get_object_id(rel.left)

        return data

    def field_to_native(self, obj, field_name):
        # Group relationships by type to facilitate cleaner template rendering

        has_parent = self.parent and hasattr(self.parent.opts, 'model')
        if not has_parent:
            return super(RelationshipSerializer, self).field_to_native(obj, field_name)

        groups = {}
        rels = getattr(obj, field_name).all()

        for rel in rels:
            data = self.to_native(rel)
            if data['type'] not in groups:
                groups[data['type']] = []
            groups[data['type']].append(data)
            del data['type']

        return [
            {
                'type': key,
                'list': val
            } for key, val in groups.items()
        ]

app.router.register_serializer(Relationship, RelationshipSerializer)
