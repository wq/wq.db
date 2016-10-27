from rest_framework import serializers
from django.contrib.gis.db import models as model_fields
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone

from django.conf import settings

from .model_tools import get_object_id, get_by_identifier

from rest_framework.utils import model_meta
from html_json_forms.serializers import JSONFormSerializer


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


class LabelRelatedField(serializers.RelatedField):
    def to_representation(self, obj):
        return str(obj)


# TODO: investigate use of SlugRelatedField and/or PrimaryKeyRelatedField
class IDRelatedField(serializers.RelatedField):
    def to_representation(self, obj):
        return get_object_id(obj)

    def to_internal_value(self, data):
        return get_by_identifier(self.queryset, data)


class LocalDateTimeField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if value is None:
            return None
        if value.tzinfo:
            value = timezone.localtime(value)
        return value.strftime('%Y-%m-%d %I:%M %p')


class BaseModelSerializer(JSONFormSerializer, serializers.ModelSerializer):
    xlsform_types = {
        serializers.FileField: 'binary',
        serializers.DateField: 'date',
        serializers.DateTimeField: 'dateTime',
        serializers.FloatField: 'decimal',
        GeometryField: 'geoshape',
        serializers.IntegerField: 'int',
        serializers.CharField: 'string',
        serializers.ChoiceField: 'select1',
        serializers.TimeField: 'time',
    }

    def get_fields_for_config(self):
        fields = self.get_fields()
        for name, field in list(fields.items()):
            if name == 'id' or field.read_only:
                fields.pop(name)
        return fields

    def get_wq_config(self):
        fields = []
        nested_fields = []
        has_geo_fields = False

        overrides = getattr(self.Meta, 'wq_field_config', {})

        for name, field in self.get_fields_for_config().items():
            info = self.get_wq_field_info(name, field)

            if info['type'].startswith('geo') or info['name'] == 'latitude':
                has_geo_fields = True

            if info['name'] in overrides:
                info.update(overrides[info['name']])

            if info['type'] == 'repeat':
                nested_fields.append(info)
            else:
                fields.append(info)

        config = getattr(self.Meta, 'wq_config', {}).copy()
        config['form'] = fields + nested_fields
        if 'name' not in config:
            config['name'] = self.Meta.model._meta.model_name
        if has_geo_fields and 'map' not in config:
            config['map'] = True
        if 'label_template' not in config:
            label_template = getattr(
                self.Meta.model, 'wq_label_template', None
            )
            if label_template:
                config['label_template'] = label_template
        return config

    def get_wq_field_info(self, name, field):
        info = {
            'name': name,
            'label': field.label or name.replace('_', ' ').title(),
        }
        if field.required:
            info.setdefault('bind', {})
            info['bind']['required'] = True

        if field.help_text:
            info['hint'] = field.help_text

        if isinstance(field, serializers.ChoiceField):
            info['choices'] = [{
                'name': cname,
                'label': label,
            } for cname, label in field.choices.items()]
        elif getattr(field, 'max_length', None):
            info['wq:length'] = field.max_length

        if isinstance(field, serializers.ListSerializer):
            # Nested model with a foreign key to this one
            field.child.context['router'] = self.router
            child_config = field.child.get_wq_config()
            info['type'] = 'repeat'
            info['children'] = child_config['form']
            if 'initial' in child_config:
                info['initial'] = child_config['initial']

        elif isinstance(field, serializers.RelatedField):
            # Foreign key to a parent model
            info['type'] = 'string'
            info['name'] = info['name'].replace('_id', '')
            info['label'] = info['label'].replace(' Id', '')
            if field.queryset:
                fk = self.get_wq_foreignkey_info(field.queryset.model)
                if fk:
                    info['wq:ForeignKey'] = fk

        if 'type' not in info:
            info['type'] = 'string'
            for field_type, xlsform_type in self.xlsform_types.items():
                if isinstance(field, field_type):
                    info['type'] = xlsform_type
                    break
        return info

    def get_wq_foreignkey_info(self, model):
        if not self.router or not self.router.model_is_registered(model):
            return None
        else:
            serializer = self.router.get_serializer_for_model(
                model
            )
            model_conf = serializer().get_wq_config()
            return model_conf['name']

    class Meta:
        wq_config = {}
        wq_field_config = {}


class ModelSerializer(BaseModelSerializer):
    serializer_related_field = IDRelatedField
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

    @property
    def is_html(self):
        request = self.context.get('request', None)
        if not request:
            return
        if request.accepted_renderer.format == 'html':
            return True
        return False

    def get_fields(self, *args, **kwargs):
        fields = super(ModelSerializer, self).get_fields(*args, **kwargs)
        fields = self.update_id_fields(fields)
        fields.update(self.get_label_fields(fields))
        if not self.is_detail:
            for field in getattr(self.Meta, 'list_exclude', []):
                fields.pop(field, None)
            if self.is_html:
                for field in getattr(self.Meta, 'html_list_exclude', []):
                    fields.pop(field, None)
        return fields

    def update_id_fields(self, fields):
        if 'id' not in self.fields:
            lookup = getattr(self.Meta, 'wq_config', {}).get('lookup', None)
            if lookup and lookup != 'id':
                fields['id'] = serializers.ReadOnlyField(source=lookup)

        info = model_meta.get_field_info(self.Meta.model)

        # In list views, remove [fieldname] as an attribute in favor of
        # [fieldname]_id.
        for name, field in info.forward_relations.items():
            include = getattr(self.Meta, "fields", [])
            if include == "__all__":
                include = []
            exclude = getattr(self.Meta, "exclude", [])
            if name in exclude or (include and name not in include):
                fields.pop(name, None)
                continue

            if name + '_id' not in fields:
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
                'read_only': True,
            }
            if field_kwargs.get('many', None):
                label_field_kwargs['many'] = field_kwargs['many']
            fields[name + '_label'] = LabelRelatedField(**label_field_kwargs)

        return fields

    @classmethod
    def for_model(cls, model_class, include_fields=None):
        class Serializer(cls):
            class Meta(getattr(cls, 'Meta', object)):
                model = model_class
                if include_fields:
                    fields = include_fields
        return Serializer

    @classmethod
    def for_depth(cls, serializer_depth):
        class Serializer(cls):
            class Meta(getattr(cls, 'Meta', object)):
                depth = serializer_depth
        return Serializer

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
