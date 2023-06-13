from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.conf import settings
import re


APP_TEMPLATES = {}
SRID = 4326


def load_app_template(template_name):
    with open(template_name) as f:
        template = f.read()
    template = re.sub(
        "<title>(.+)</title>", "<title>{{title}}</title>", template
    )
    if "{{" in template:
        return template, True
    else:
        return template, False


def get_title(data, request):
    title = None
    if isinstance(data, dict):
        title = data.get("label")

    return title or settings.PROJECT_NAME


def render_app(template_name, data, request):
    if template_name not in APP_TEMPLATES:
        APP_TEMPLATES[template_name] = load_app_template(template_name)

    template, has_title = APP_TEMPLATES[template_name]
    if has_title:
        from wq.db.rest import router

        return template.replace("{{title}}", get_title(data, request)).replace(
            "{{base_url}}", router.get_base_url()
        )
    else:
        return template


class HTMLRenderer(TemplateHTMLRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if getattr(settings, "WQ_APP_TEMPLATE", None):
            return render_app(
                settings.WQ_APP_TEMPLATE,
                data,
                (renderer_context or {}).get("request"),
            )
        return super().render(data, accepted_media_type, renderer_context)


class ESMRenderer(JSONRenderer):
    media_type = "application/javascript"
    format = "js"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        data = super().render(data, accepted_media_type, renderer_context)
        return b"const config = " + data + b";\nexport default config;"


class GeoJSONRenderer(JSONRenderer):
    media_type = "application/geo+json"
    format = "geojson"

    def render(self, data, *args, **kwargs):
        if isinstance(data, list):
            features, simple = self.render_features(data)
            data = {"type": "FeatureCollection", "features": features}
        elif "list" in data and isinstance(data["list"], list):
            features, simple = self.render_features(data["list"])
            data["type"] = "FeatureCollection"
            data["features"] = features
            del data["list"]

        else:
            data, simple = self.render_feature(data)

        if not simple and getattr(settings, "SRID", SRID) != SRID:
            data["crs"] = {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:EPSG::%s" % settings.SRID
                },
            }
        return super().render(data, *args, **kwargs)

    def render_feature(self, obj):
        feature = {"type": "Feature", "properties": obj}
        simple = False
        if "id" in obj:
            feature["id"] = obj["id"]
            del obj["id"]

        if "latitude" in obj and "longitude" in obj:
            feature["geometry"] = {
                "type": "Point",
                "coordinates": [obj["longitude"], obj["latitude"]],
            }
            del obj["latitude"]
            del obj["longitude"]
            simple = True

        else:
            for key, val in list(obj.items()):
                if (
                    isinstance(val, dict)
                    and "type" in val
                    and ("coordinates" in val or "geometries" in val)
                ):
                    feature["geometry"] = val
                    del obj[key]

        if "features" in obj:
            feature["features"] = obj["features"]
            feature["type"] = "FeatureCollection"
            del obj["features"]

        return feature, simple

    def render_features(self, objs):
        features = []
        has_simple = False
        for obj in objs:
            feature, simple = self.render_feature(obj)
            if simple:
                has_simple = True
                if feature["geometry"]["coordinates"][0] is not None:
                    features.append(feature)
            else:
                features.append(feature)
        return features, has_simple
