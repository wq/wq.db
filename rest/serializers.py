from rest_framework import serializers
from django.contrib.gis.db import models as model_fields
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone

from django.conf import settings

from .models import ContentType, get_ct

from rest_framework.utils import model_meta
from . import compat as html


class GeometryField(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        import json
        return json.loads(value.geojson)

    def to_internal_value(self, value):
        import json
        if isinstance(value, dict):
            value = json.dumps(value)
        geom = GEOSGeometry(value)
        srid = getattr(settings, 'SRID', 4326)

        if 'crs' in value and value['crs'].get('type', None) == 'name':
            name = value['crs']['properties']['name']
            if name.startswith('urn:ogc:def:crs:EPSG::'):
                geom.srid = int(name.replace('urn:ogc:def:crs:EPSG::', ''))

        if geom.srid is None:
            geom.srid = 4326
        if geom.srid != srid:
            geom.transform(srid)
        return geom


class LookupRelatedField(serializers.SlugRelatedField):
    def __init__(self, router, model, **kwargs):
        self.router = router
        self.model = model
        super(serializers.SlugRelatedField, self).__init__(**kwargs)

    @property
    def slug_field(self):
        if not self.router:
            return 'pk'
        return self.router.get_lookup_for_model(self.model)


class ContentTypeField(serializers.SlugRelatedField):
    queryset = ContentType.objects.all()
    slug_field = "model"

    def __init__(self, **kwargs):
        super(serializers.RelatedField, self).__init__(**kwargs)


class LocalDateTimeField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if value is None:
            return None
        if value.tzinfo:
            value = timezone.localtime(value)
        return value.strftime('%Y-%m-%d %I:%M %p')


class ModelSerializer(serializers.ModelSerializer):
    add_label_fields = True

    def __init__(self, *args, **kwargs):
        for field in ('Geometry', 'GeometryCollection',
                      'Point', 'LineString', 'Polygon',
                      'MultiPoint', 'MultiLineString', 'MultiPolygon'):
            self.serializer_field_mapping[
                getattr(model_fields, field + 'Field')
            ] = GeometryField
        super(ModelSerializer, self).__init__(*args, **kwargs)

    @property
    def router(self):
        if 'view' not in self.context and 'router' not in self.context:
            return None
        if 'view' in self.context:
            return self.context['view'].router
        else:
            return self.context['router']

    @property
    def is_detail(self):
        if getattr(self.Meta, 'depth', 0) > 0:
            return True
        view = self.context.get('view', None)
        return view and view.action != "list"

    @property
    def is_edit(self):
        view = self.context.get('view', None)
        return view and view.action == 'edit'

    @property
    def is_geojson(self):
        request = self.context.get('request', None)
        if not request:
            return
        if request.accepted_renderer.format == 'geojson':
            return True
        return False

    def get_fields(self, *args, **kwargs):
        fields = super(ModelSerializer, self).get_fields(*args, **kwargs)
        fields = self.update_id_fields(fields)
        fields.update(self.get_label_fields(fields))
        if not self.is_detail:
            for field in getattr(self.Meta, 'list_exclude', []):
                fields.pop(field, None)
        return fields

    def update_id_fields(self, fields):
        if 'id' not in self.fields:
            conf = get_ct(self.Meta.model).get_config() or {}
            lookup = conf.get('lookup', None)
            if lookup and lookup != 'id':
                fields['id'] = serializers.ReadOnlyField(source=lookup)

        info = model_meta.get_field_info(self.Meta.model)

        # In list views, remove [fieldname] as an attribute in favor of
        # [fieldname]_id.
        for name, field in info.forward_relations.items():
            include = getattr(self.Meta, "fields", [])
            exclude = getattr(self.Meta, "exclude", [])
            if name in exclude or (include and name not in include):
                fields.pop(name, None)
                continue

            id_field, id_field_kwargs = self.build_relational_field(
                name, field
            )
            id_field_kwargs['source'] = name
            fields[name + '_id'] = id_field(**id_field_kwargs)

            if name in fields:
                # Update/remove DRF default foreign key field (w/o _id)
                if self.is_detail and isinstance(
                        fields[name], serializers.Serializer):
                    # Nested representation, keep for detail template context
                    fields[name].read_only = True
                else:
                    # Otherwise we don't need this field
                    del fields[name]

        return fields

    def get_label_fields(self, default_fields):
        if not self.add_label_fields:
            return {}
        fields = {}

        exclude = getattr(self.Meta, 'exclude', [])
        if 'label' not in exclude and 'label' not in default_fields:
            fields['label'] = serializers.ReadOnlyField(source='__str__')

        info = model_meta.get_field_info(self.Meta.model)

        # Add labels for dates and fields with choices
        for name, field in info.fields.items():
            if isinstance(field, model_fields.DateTimeField):
                fields[name + '_label'] = LocalDateTimeField(source=name)
            if field.choices:
                fields[name + '_label'] = serializers.ReadOnlyField(
                    source='get_%s_display' % name
                )

        # Add labels for related fields
        for name, field in info.forward_relations.items():
            if name in getattr(self.Meta, "exclude", []):
                continue

            f, field_kwargs = self.build_relational_field(
                name, info.forward_relations[name],
            )
            label_field_kwargs = {
                'source': name,
            }
            if field_kwargs.get('many', None):
                label_field_kwargs['many'] = field_kwargs['many']
            fields[name + '_label'] = serializers.StringRelatedField(
                **label_field_kwargs
            )

        return fields

    @classmethod
    def for_model(cls, model_class):
        class Serializer(cls):
            class Meta(getattr(cls, 'Meta', object)):
                model = model_class
        return Serializer

    @classmethod
    def for_depth(cls, serializer_depth):
        class Serializer(cls):
            class Meta(getattr(cls, 'Meta', object)):
                depth = serializer_depth
        return Serializer

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(
            ModelSerializer, self
        ).build_relational_field(field_name, relation_info)
        if field_class == self.serializer_related_field:
            field_class = LookupRelatedField
            field_kwargs['router'] = self.router
            field_kwargs['model'] = relation_info.related_model
        return field_class, field_kwargs

    def build_nested_field(self, field_name, relation_info, nested_depth):
        field_class, field_kwargs = super(
            ModelSerializer, self
        ).build_nested_field(
            field_name, relation_info, nested_depth
        )
        field_kwargs['required'] = False
        if self.router:
            field_class = self.router.get_serializer_for_model(
                relation_info.related_model, nested_depth
            )
        return field_class, field_kwargs

    def to_internal_value(self, data):
        if html.is_html_input(data):
            data = html.parse_json_form(data)
        return super(ModelSerializer, self).to_internal_value(data)
