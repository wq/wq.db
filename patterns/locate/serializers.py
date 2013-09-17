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

    def from_native(self, data, files):
        if (data.get('type', None) == 'Feature'
                and 'properties' in data and 'geometry' in data):
            obj = data['properties']
            obj['geometry'] = data['geometry']
            if 'id' in data:
                obj['id'] = data['id']
            if 'crs' in data:
                obj['geometry']['crs'] = data['crs']
        return super(LocationSerializer, self).from_native(data, files)

    def field_to_native(self, obj, field_name):
        if not self.as_geometry:
            return super(LocationSerializer, self).field_to_native(
                obj, field_name
            )

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
        vals = data.get(field_name, None)
        if isinstance(vals, basestring) and vals.strip() != '':
            vals = json.loads(vals)
        if (isinstance(vals, dict) and
                vals.get('type', None) == "FeatureCollection"):
            if 'crs' in vals:
                features = []
                for feature in vals['features']:
                    feature.update({
                        'crs': vals['crs']
                    })
                    features.append(feature)
            else:
                features = vals['features']
            data = {field_name: features}
        else:
            data = {field_name: []}
        return super(LocationSerializer, self).field_from_native(
            data, files, field_name, into
        )

    class Meta:
        exclude = ('content_type_id', 'for', 'object_id')

app.router.register_serializer(Location, LocationSerializer)
