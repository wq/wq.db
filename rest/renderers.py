from rest_framework.renderers import JSONRenderer
from django.conf import settings
from wq.db.default_settings import SRID as DEFAULT_SRID


class JSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context and 'request' in renderer_context:
            if not renderer_context['request'].is_ajax():
                renderer_context['indent'] = 4
        return super(JSONRenderer, self).render(
            data, accepted_media_type, renderer_context
        )


class GeoJSONRenderer(JSONRenderer):
    media_type = 'application/geo+json'
    format = 'geojson'

    def render(self, data, *args, **kwargs):
        if isinstance(data, list):
            features, simple = self.render_features(data)
            data = {
                'type': 'FeatureCollection',
                'features': features
            }
        elif "list" in data and isinstance(data['list'], list):
            features, simple = self.render_features(data['list'])
            data['type'] = 'FeatureCollection'
            data['features'] = features
            del data['list']

        else:
            data, simple = self.render_feature(data)

        if not simple and getattr(settings, 'SRID', None) != DEFAULT_SRID:
            data['crs'] = {
                'type': 'name',
                'properties': {
                    'name': 'urn:ogc:def:crs:EPSG::%s' % settings.SRID
                }
            }
        return super(GeoJSONRenderer, self).render(data, *args, **kwargs)

    def render_feature(self, obj):
        feature = {
            'type': 'Feature',
            'properties': obj
        }
        simple = False
        if 'id' in obj:
            feature['id'] = obj['id']
            del obj['id']

        if 'latitude' in obj and 'longitude' in obj:
            feature['geometry'] = {
                'type': 'Point',
                'coordinates': [obj['longitude'], obj['latitude']]
            }
            del obj['latitude']
            del obj['longitude']
            simple = True

        else:
            for key, val in list(obj.items()):
                if isinstance(val, dict) and 'type' in val and (
                        'coordinates' in val or 'geometries' in val
                        ):
                    feature['geometry'] = val
                    del obj[key]

        if 'features' in obj:
            feature['features'] = obj['features']
            feature['type'] = 'FeatureCollection'
            del obj['features']

        return feature, simple

    def render_features(self, objs):
        features = []
        has_simple = False
        for obj in objs:
            feature, simple = self.render_feature(obj)
            if simple:
                has_simple = True
                if feature['geometry']['coordinates'][0] is not None:
                    features.append(feature)
            else:
                features.append(feature)
        return features, has_simple
