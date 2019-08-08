from rest_framework import serializers
from django.core.exceptions import ImproperlyConfigured
try:
    from django.contrib.gis.db import models as model_fields
    from django.contrib.gis.geos import GEOSGeometry
except (OSError, ImproperlyConfigured):
    from django.db import models as model_fields
    GEOSGeometry = None

from django.utils import timezone
from django.core.exceptions import FieldDoesNotExist
from collections import OrderedDict

from django.conf import settings

from rest_framework.utils import model_meta
from html_json_forms.serializers import JSONFormSerializer
from .model_tools import get_object_id
from .exceptions import ImproperlyConfigured


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

        if not GEOSGeometry:
            raise Exception("Missing GDAL")

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


class LocalDateTimeField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if value is None:
            return None
        if value.tzinfo:
            value = timezone.localtime(value)
        return value.strftime('%Y-%m-%d %I:%M %p')


MODEL_BOOLEAN_FIELDS = (
    model_fields.BooleanField,
    model_fields.NullBooleanField,
)


class BooleanLabelField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if value is None:
            return None
        elif value:
            return 'Yes'
        else:
            return 'No'


class BlankCharField(serializers.CharField):
    def run_validation(self, data=serializers.empty):
        if self.allow_blank and data is None:
            return ''
        return super(BlankCharField, self).run_validation(data)


class BaseModelSerializer(JSONFormSerializer, serializers.ModelSerializer):
    xlsform_types = OrderedDict((
        (serializers.ImageField, 'image'),
        (serializers.FileField, 'binary'),
        (serializers.DateField, 'date'),
        (serializers.DateTimeField, 'dateTime'),
        (serializers.FloatField, 'decimal'),
        (GeometryField, 'geoshape'),
        (serializers.IntegerField, 'int'),
        (serializers.CharField, 'string'),
        (serializers.ChoiceField, 'select one'),
        (serializers.TimeField, 'time'),
    ))

    def get_fields_for_config(self):
        self._for_wq_config = True
        fields = self.get_fields()
        del self._for_wq_config
        for name, field in list(fields.items()):
            if name == 'id' or field.read_only:
                fields.pop(name)
            elif isinstance(field, serializers.NullBooleanField):
                fields[name] = serializers.ChoiceField(
                    choices=self.get_boolean_choices(field),
                    required=False,
                )
            elif isinstance(field, serializers.BooleanField):
                fields[name] = serializers.ChoiceField(
                    choices=self.get_boolean_choices(field),
                    required=field.required,
                )
        return fields

    def get_boolean_choices(self, field):
        return [(True, 'Yes'), (False, 'No')]

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

    def get_wq_field_info(self, name, field, model=None):
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
            if not isinstance(field, serializers.FileField):
                info['wq:length'] = field.max_length

        if isinstance(field, serializers.ListSerializer):
            # Nested model with a foreign key to this one
            field.child.context['router'] = self.router
            if hasattr(field.child, 'get_wq_config'):
                child_config = field.child.get_wq_config()
            else:
                child_config = {'form': []}
            info['type'] = 'repeat'
            info['children'] = child_config['form']
            if 'initial' in child_config:
                info['initial'] = child_config['initial']

        elif isinstance(field, serializers.RelatedField):
            # Foreign key to a parent model
            info['type'] = 'string'
            info['name'] = info['name'].replace('_id', '')
            info['label'] = info['label'].replace(' Id', '')
            if hasattr(field, 'queryset'):
                fk = self.get_wq_foreignkey_info(field.queryset.model)
                if fk:
                    info['wq:ForeignKey'] = fk

        if 'type' not in info:
            info['type'] = 'string'

            for field_type, xlsform_type in self.xlsform_types.items():
                if isinstance(field, field_type):
                    info['type'] = xlsform_type
                    break

            if info['type'] == 'geoshape':
                model = model or self.Meta.model
                source = model._meta.get_field(name)
                if info['type'] == 'geoshape':
                    geom_type = getattr(source, 'geom_type', None)
                    if geom_type == 'POINT':
                        info['type'] = 'geopoint'
                    elif geom_type == 'LINESTRING':
                        info['type'] = 'geotrace'

            if info['type'] == 'string':
                model = model or self.Meta.model
                try:
                    source = model._meta.get_field(name)
                except FieldDoesNotExist:
                    pass
                else:
                    if source.get_internal_type() == "TextField":
                        info['type'] = "text"

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
    add_label_fields = True

    def __init__(self, *args, **kwargs):
        mapping = self.serializer_field_mapping

        for model_field, serializer_field in list(mapping.items()):
            if serializer_field == serializers.CharField:
                mapping[model_field] = BlankCharField

        if GEOSGeometry:
            for field in ('Geometry', 'GeometryCollection',
                          'Point', 'LineString', 'Polygon',
                          'MultiPoint', 'MultiLineString', 'MultiPolygon'):
                mapping[getattr(model_fields, field + 'Field')] = GeometryField
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

    @property
    def is_config(self):
        return getattr(self, '_for_wq_config', False)

    def get_fields(self, *args, **kwargs):
        fields = super(ModelSerializer, self).get_fields(*args, **kwargs)
        fields = self.update_id_fields(fields)
        fields.update(self.get_label_fields(fields))
        exclude = set()

        def get_exclude(meta_name):
            return set(getattr(self.Meta, meta_name, []))

        if not self.is_detail and not self.is_config:
            exclude |= get_exclude('list_exclude')
            if self.is_html:
                exclude |= get_exclude('html_list_exclude')

        if self.is_config:
            exclude |= get_exclude('config_exclude')

        for field in list(exclude):
            fields.pop(field, None)

        return fields

    def update_id_fields(self, fields):
        if 'id' not in self._declared_fields:
            lookup = getattr(self.Meta, 'wq_config', {}).get('lookup', None)
            if lookup and lookup != 'id':
                fields['id'] = serializers.ReadOnlyField(source=lookup)

        id_fields = {}
        info = model_meta.get_field_info(self.Meta.model)

        # In list views, remove [fieldname] as an attribute in favor of
        # [fieldname]_id.
        extra_kwargs = self.get_extra_kwargs()
        for name, field in info.forward_relations.items():
            include = getattr(self.Meta, "fields", [])
            if include == "__all__":
                include = []
            exclude = getattr(self.Meta, "exclude", [])
            if name in exclude or (include and name not in include):
                fields.pop(name, None)
                continue

            default_field = fields[name]
            auto_related_field = (serializers.Serializer, LookupRelatedField)
            if not isinstance(default_field, auto_related_field):
                continue

            if name + '_id' not in fields:
                id_field, id_field_kwargs = self.build_relational_field(
                    name, field
                )
                extra_field_kwargs = extra_kwargs.get(name, {})
                extra_field_kwargs.update(
                    extra_kwargs.get(name + '_id', {})
                )
                self.include_extra_kwargs(
                    id_field_kwargs,
                    extra_field_kwargs,
                )
                id_field_kwargs['source'] = name
                id_fields[name] = id_field(**id_field_kwargs)

            if name in fields:
                # Update/remove DRF default foreign key field (w/o _id)
                if self.is_detail and isinstance(
                        default_field, serializers.Serializer):
                    # Nested representation, keep for detail template context
                    fields[name].read_only = True
                else:
                    # Otherwise we don't need this field
                    del fields[name]

        if not id_fields:
            return fields

        # Ensure _id fields show up in the same order they appear on model
        updated_fields = OrderedDict()
        for field in self.Meta.model._meta.fields:
            name = field.name
            if name in fields:
                updated_fields[name] = fields.pop(name)
            if name in id_fields:
                updated_fields[name + '_id'] = id_fields.pop(name)

        if fields:
            updated_fields.update(fields)

        if id_fields:
            for name in id_fields:
                updated_fields[name + '_id'] = id_fields[name]

        return updated_fields

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
            if name in getattr(self.Meta, "exclude", []):
                continue
            if name + '_label' in default_fields:
                continue
            if isinstance(field, model_fields.DateTimeField):
                fields[name + '_label'] = LocalDateTimeField(source=name)
            if field.choices:
                fields[name + '_label'] = serializers.ReadOnlyField(
                    source='get_%s_display' % name
                )
            if isinstance(field, MODEL_BOOLEAN_FIELDS):
                fields[name + '_label'] = BooleanLabelField(
                    source=name,
                )

        # Add labels for related fields
        for name, field in info.forward_relations.items():
            if name in getattr(self.Meta, "exclude", []):
                continue
            if name + '_label' in default_fields:
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

    def build_relational_field(self, field_name, relation_info):
        if isinstance(relation_info.related_model, str):
            raise ImproperlyConfigured(
                "%s could not be resolved to a model class"
                % relation_info.related_model,
            )

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

    def add_lookups(self, context):
        # Mimic _addLookups in wq.app/app.js
        if not self.router:
            return

        conf = self.get_wq_config()
        for field in conf['form']:
            if 'choices' in field:
                # CharField choices
                context[field['name'] + '_choices'] = [{
                    'name': choice['name'],
                    'label': choice['label'],
                    'selected': (
                        choice['name'] == context.get(field['name'], '')
                    ),
                } for choice in field['choices']]

            elif 'wq:ForeignKey' in field:
                choices = self.get_lookup_choices(field, context)
                if choices:
                    context[field['name'] + '_list'] = choices

            elif 'children' in field:
                rows = context.get(field['name'])
                if isinstance(rows, list) and len(rows) > 0:
                    serializer = self.get_fields().get(field['name'])
                    serializer.child.context.update(
                        router=self.router,
                        request=self.context.get('request')
                    )
                    if serializer and hasattr(serializer.child, 'add_lookups'):
                        for row in rows:
                            serializer.child.add_lookups(row)

    def get_lookup_choices(self, field, context):
        model_name = field['wq:ForeignKey']
        model_conf = self.router.get_model_config(field['wq:ForeignKey'])
        if not model_conf:
            return

        qs = self.router.get_queryset_for_model(
            model_name, self.context.get('request')
        )
        if field.get('filter', None):
            qs = qs.filter(**self.compute_filter(
                field['filter'],
                model_conf,
                context
            ))
        choices = self.serialize_choices(qs, field)
        self.set_selected(choices, context.get(field['name'] + '_id', ''))
        return choices

    def compute_filter(self, filter, model_conf, context):
        def render(value):
            import pystache
            result = pystache.render(value, context)
            if result == '':
                return None
            elif result.isdigit():
                result = int(result)
            return result

        fk_lookups = {}
        for field in model_conf['form']:
            if 'wq:ForeignKey' not in field:
                continue
            lookup = self.router.get_lookup_for_model(
                field['wq:ForeignKey']
            )
            if lookup and lookup != 'pk':
                fk_lookups['%s_id' % field['name']] = '%s__%s' % (
                    field['name'], lookup
                )

        computed_filter = {}
        for key, values in filter.items():
            if not isinstance(values, list):
                values = [values]
            values = [
                render(value) if '{{' in value else value
                for value in values
            ]

            if key in fk_lookups:
                key = fk_lookups[key]

            if len(values) > 1:
                computed_filter[key + '__in'] = values
            else:
                computed_filter[key] = values[0]

        return computed_filter

    def serialize_choices(self, qs, field):
        return [{
            'id': get_object_id(obj),
            'label': str(obj)
        } for obj in qs]

    def set_selected(self, choices, value):
        for choice in choices:
            if choice['id'] == value:
                choice['selected'] = True
