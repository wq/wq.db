from wq.db.rest.serializers import ModelSerializer
from wq.db.rest import app
from wq.db.rest.models import get_ct, get_object_id

import json

from .models import Location

class LocationSerializer(ModelSerializer):

    @property
    def as_geometry(self):
        if 'request' in self.context:
            renderer = self.context['request'].accepted_renderer
            if renderer.format == 'geojson':
                return True
        return False

    def to_native(self, loc):
        has_parent = self.parent and hasattr(self.parent.opts, 'model')
        if self.as_geometry and has_parent:
            return json.loads(loc.geometry.geojson)

        data = super(LocationSerializer, self).to_native(loc)
        if has_parent:
            pass
        else:
            # Include pointer to parent object (see annotate/serializers.py)
            idname = get_ct(loc.content_object).identifier + '_id'
            data[idname] = get_object_id(loc.content_object)
        return data


    def field_to_native(self, obj, field_name):
        if not self.as_geometry:
            return super(LocationSerializer, self).field_to_native(obj, field_name)

        loc = getattr(obj, field_name or self.source)
        if loc.count() == 1:
            return self.to_native(loc.all()[0])
        elif loc.count() > 1:
            return {
                'type': 'GeometryCollection',
                'geometries': [
                    self.to_native(l) for l in loc.all()
                ]
            }
        else:
            return None

    def field_from_native(self, data, files, field_name, into):
        # FIXME: not supported; set to empty array to avoid validation error
        into[field_name] = []

    class Meta:
        exclude = ('content_type_id', 'for', 'object_id')

app.router.register_serializer(Location, LocationSerializer)
