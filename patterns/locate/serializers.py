from wq.db.rest.models import get_ct, get_object_id
from wq.db.patterns.base import serializers as base
from django.utils.six import string_types
import json
from .models import Location


class LocationListSerializer(base.AttachmentListSerializer):
    def to_representation(self, data):
        data = super(LocationListSerializer, self).to_representation(data)
        if not self.child.is_geojson:
            return data

        if self.child.as_geometry:
            if len(data) == 1:
                return data[0]
            elif len(data) > 1:
                return {
                    'type': 'GeometryCollection',
                    'geometries': data
                }
            else:
                return None
        else:
            features = []
            for loc in data:
                feat = {
                    'id': loc['id'],
                    'type': 'Feature',
                    'geometry': loc['geometry'],
                    'properties': loc
                }
                del loc['geometry']
                del loc['id']
                features.append(feat)
            return features

    def get_value(self, dictionary):
        vals = dictionary.get(self.field_name, None)
        if isinstance(vals, string_types) and vals.strip() != '':
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
        else:
            features = []

        return features


class LocationSerializer(base.AttachmentSerializer):
    def __init__(self, as_geometry=False, **kwargs):
        self.as_geometry = as_geometry
        super(LocationSerializer, self).__init__(**kwargs)

    def to_representation(self, loc):
        has_parent = (
            self.parent and self.parent.parent and
            hasattr(self.parent.parent.Meta, 'model')
        )
        if self.as_geometry and has_parent:
            return json.loads(loc.geometry.geojson)

        data = super(LocationSerializer, self).to_representation(loc)
        if has_parent:
            pass
        else:
            # Include pointer to parent object (see annotate/serializers.py)
            idname = get_ct(loc.content_object).identifier + '_id'
            data[idname] = get_object_id(loc.content_object)
        return data

    def to_internal_value(self, data):
        if (data.get('type', None) == 'Feature' and
                'properties' in data and 'geometry' in data):
            obj = data['properties']
            obj['geometry'] = data['geometry']
            if 'id' in data:
                obj['id'] = data['id']
            if 'crs' in data:
                obj['geometry']['crs'] = data['crs']
            data = obj
        return super(LocationSerializer, self).to_internal_value(data)

    class Meta:
        exclude = ('content_type', 'object_id')
        model = Location
        list_serializer_class = LocationListSerializer


class LocatedModelSerializer(base.AttachedModelSerializer):
    locations = LocationSerializer(many=True)

    def get_fields(self):
        fields = super(LocatedModelSerializer, self).get_fields()
        if self.is_geojson:
            # Rename locations to "features" or "geometry" for use as GeoJSON
            locations = fields.pop('locations')
            if self.is_edit:
                name = 'features'
            else:
                name = 'geometry'
                locations.child.as_geometry = True
            locations.source = 'locations'
            fields[name] = locations
        elif not self.is_detail:
            fields.pop('locations')
        return fields

    class Meta:
        wq_config = {
            'map': True,
        }
