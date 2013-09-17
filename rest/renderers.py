from rest_framework.renderers import BaseRenderer, JSONPRenderer, JSONRenderer
from django.conf import settings


class JSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context and 'request' in renderer_context:
            if not renderer_context['request'].is_ajax():
                renderer_context['indent'] = 4
        return super(JSONRenderer, self).render(
            data, accepted_media_type, renderer_context
        )


class AMDRenderer(JSONPRenderer):
    media_type = 'application/javascript'
    format = 'js'
    default_callback = 'define'


class BinaryRenderer(BaseRenderer):
    def render(self, data, media_type=None, render_context=None):
        return data


def binary_renderer(mimetype, extension=None):
    class Renderer(BinaryRenderer):
        media_type = mimetype
        format = extension
    return Renderer


class GeoJSONRenderer(JSONRenderer):
    media_type = 'application/json'
    format = 'geojson'
    disable_pagination = True

    def render(self, data, *args, **kwargs):
        if isinstance(data, list):
            data = {
                'type': 'FeatureCollection',
                'features': [
                    self.render_feature(feature) for feature in data
                ]
            }
        else:
            data = self.render_feature(data)

        if hasattr(settings, 'SRID') and settings.SRID != 3857:
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

        elif 'geometry' in obj:
            feature['geometry'] = obj['geometry']
            del obj['geometry']

        elif 'locations' in obj:
            feature['geometry'] = obj['locations']
            del obj['locations']

        return feature
