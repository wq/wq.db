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
from html_json_forms.serializers import parse_json_form
from natural_keys.serializers import (
    NaturalKeyModelSerializer,
    NaturalKeySerializer,
)
from drf_writable_nested import WritableNestedModelSerializer
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
        srid = getattr(settings, "SRID", 4326)

        if "crs" in value and value["crs"].get("type", None) == "name":
            name = value["crs"]["properties"]["name"]
            if name.startswith("urn:ogc:def:crs:EPSG::"):
                geom.srid = int(name.replace("urn:ogc:def:crs:EPSG::", ""))

        if geom.srid is None:
            geom.srid = 4326
        if geom.srid != srid:
            geom.transform(srid)
        return geom


class LookupRelatedField(serializers.SlugRelatedField):
    def __init__(self, router, model, **kwargs):
        self.router = router
        self.model = model
        self._slug_field = kwargs.pop("slug_field", None)
        super(serializers.SlugRelatedField, self).__init__(**kwargs)

    @property
    def slug_field(self):
        if self._slug_field:
            return self._slug_field
        elif self.router:
            return self.router.get_lookup_for_model(self.model)
        else:
            return "pk"

    def use_pk_only_optimization(self):
        if self.slug_field == "pk":
            return True
        if self.parent and self.parent.Meta.model:
            model_field = self.parent.Meta.model._meta.get_field(
                self.source_attrs[-1]
            )
            if model_field.target_field.name == self.slug_field:
                return True
        return False

    def get_attribute(self, instance):
        value = super().get_attribute(instance)
        if self.slug_field != "pk" and isinstance(
            value, serializers.PKOnlyObject
        ):
            setattr(value, self.slug_field, value.pk)
        return value


class LocalDateTimeField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if value is None:
            return None
        if value.tzinfo:
            value = timezone.localtime(value)
        return value.strftime("%Y-%m-%d %I:%M %p")


MODEL_BOOLEAN_FIELDS = (
    model_fields.BooleanField,
    model_fields.NullBooleanField,
)


class BooleanLabelField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if value is None:
            return None
        elif value:
            return "Yes"
        else:
            return "No"


class BlankCharField(serializers.CharField):
    def run_validation(self, data=serializers.empty):
        if self.allow_blank and data is None:
            return ""
        return super(BlankCharField, self).run_validation(data)


def is_empty_or_url(data):
    if not data:
        return True
    if data is serializers.empty:
        return True
    if isinstance(data, str) and data.startswith(("http://", "https://")):
        return True
    return False


class ClearableFileField(serializers.FileField):
    def validate_empty_values(self, data):
        parent = self.parent
        while parent.parent and parent.instance is None:
            parent = parent.parent
        if parent.instance is not None:
            if is_empty_or_url(data):
                raise serializers.SkipField()
            elif data == "__clear__":
                data = None
        elif not data:
            data = None
        return super().validate_empty_values(data)


class ClearableImageField(ClearableFileField, serializers.ImageField):
    pass


def get_choice_list(choices, group=None):
    choice_list = []
    for key, value in choices.items():
        if isinstance(value, dict):
            choice_list += get_choice_list(value, group=key)
        else:
            choice = {
                "name": key,
                "label": value,
            }
            if group:
                choice["group"] = group
            choice_list.append(choice)
    return choice_list


class ListSerializer(serializers.ListSerializer):
    @property
    def type_field(self):
        if not hasattr(self, "_type_field"):
            initial = self.child.get_wq_config().get("initial")
            if (
                initial
                and isinstance(initial, dict)
                and "type_field" in initial
            ):
                self._type_field = initial["type_field"] + "_id"
            else:
                self._type_field = None
        return self._type_field

    def check_empty(self, val):
        return val is None or val == ""

    def skip_empty(self, row):
        if not self.type_field:
            return None
        vals = [
            val
            for key, val in row.items()
            if key != self.type_field and not self.check_empty(val)
        ]
        if not vals:
            return True
        else:
            return False

    def get_value(self, dictionary):
        value = super().get_value(dictionary)
        if isinstance(value, list):
            value = [row for row in value if not self.skip_empty(row)]
        return value


class ModelSerializer(
    NaturalKeyModelSerializer,
    WritableNestedModelSerializer,
):
    add_label_fields = True

    serializer_related_field = LookupRelatedField
    serializer_related_to_field = LookupRelatedField

    xlsform_types = OrderedDict(
        (
            (serializers.ImageField, "image"),
            (ClearableImageField, "image"),
            (serializers.FileField, "file"),
            (ClearableFileField, "file"),
            (serializers.DateField, "date"),
            (serializers.DateTimeField, "dateTime"),
            (serializers.FloatField, "decimal"),
            (GeometryField, "geoshape"),
            (serializers.IntegerField, "int"),
            (serializers.CharField, "string"),
            (serializers.ChoiceField, "select one"),
            (serializers.TimeField, "time"),
        )
    )

    def __init__(self, *args, wq_config=None, **kwargs):
        mapping = self.serializer_field_mapping
        mapping[model_fields.FileField] = ClearableFileField
        mapping[model_fields.ImageField] = ClearableImageField

        for model_field, serializer_field in list(mapping.items()):
            if serializer_field == serializers.CharField:
                mapping[model_field] = BlankCharField

        if GEOSGeometry:
            for field in (
                "Geometry",
                "GeometryCollection",
                "Point",
                "LineString",
                "Polygon",
                "MultiPoint",
                "MultiLineString",
                "MultiPolygon",
            ):
                mapping[getattr(model_fields, field + "Field")] = GeometryField
        if wq_config:
            self.wq_config = wq_config
        super().__init__(*args, **kwargs)
        if getattr(self, "initial_data", None):
            self.initial_data = parse_json_form(self.initial_data)
        self.id_fields = set()

    @classmethod
    def many_init(cls, *args, **kwargs):
        if not hasattr(cls.Meta, "list_serializer_class"):
            cls.Meta.list_serializer_class = ListSerializer
        return super().many_init(*args, **kwargs)

    def create(self, validated_data):
        self.convert_natural_keys(validated_data)
        return WritableNestedModelSerializer.create(self, validated_data)

    def update(self, instance, validated_data):
        self.convert_natural_keys(validated_data)
        return WritableNestedModelSerializer.update(
            self, instance, validated_data
        )

    def get_fields_for_config(self):
        self._for_wq_config = True
        fields = self.get_fields()
        del self._for_wq_config
        overrides = getattr(self.Meta, "wq_field_config", None) or {}

        for name, field in list(fields.items()):
            has_wq_config = False
            if name != "id" and not field.read_only and not field.write_only:
                has_wq_config = True
            elif "wq_config" in field.style:
                has_wq_config = True
            elif name in overrides:
                has_wq_config = True

            if not has_wq_config:
                fields.pop(name)
            elif isinstance(field, serializers.BooleanField):
                fields[name] = serializers.ChoiceField(
                    choices=self.get_boolean_choices(field),
                    required=field.required,
                    label=field.label,
                    help_text=field.help_text,
                )
        return fields

    def get_boolean_choices(self, field):
        return [(True, "Yes"), (False, "No")]

    def get_wq_config(self):
        serializer_fields = self.get_fields_for_config()
        fields = []
        nested_fields = []
        nested_field_dict = {}
        has_geo_fields = False

        overrides = getattr(self.Meta, "wq_field_config", None) or {}
        fieldsets = getattr(self.Meta, "wq_fieldsets", None) or {}

        def get_info(name, field):
            info = self.get_wq_field_info(name, field)
            if info["name"] in overrides:
                info.update(overrides[info["name"]])
            return info

        def pop_info(name):
            fsconf = (
                f"{type(self).__name__}.Meta.wq_fieldsets"
                f" for {self.Meta.model.__name__}"
            )
            if name in serializer_fields:
                field = serializer_fields.pop(name)
                info_name = name
            elif f"{name}_id" in serializer_fields:
                info_name = f"{name}_id"
                field = serializer_fields.pop(info_name)
            else:
                raise ImproperlyConfigured(
                    f'Unknown field "{name}" in {fsconf}'
                )

            is_fk = isinstance(
                field, (serializers.RelatedField, serializers.ManyRelatedField)
            )
            if name == info_name and is_fk:
                raise ImproperlyConfigured(
                    f'Use "{name[:-3]}" rather than "{name}"'
                    f" for ForeignKey in {fsconf}"
                )
            elif name != info_name and not is_fk:
                raise ImproperlyConfigured(
                    f'Use "{info_name}" rather than "{name}"'
                    f" for non-ForeignKey in {fsconf}"
                )
            return get_info(info_name, field)

        for name, conf in fieldsets.items():
            conf = conf.copy()
            conf.setdefault("name", name)
            conf.setdefault("type", "group")
            conf.setdefault("label", name)
            conf["children"] = [
                pop_info(name) for name in conf.pop("fields", [])
            ]
            nested_fields.append(conf)
            nested_field_dict[name] = conf

        for name, field in serializer_fields.items():
            info = get_info(name, field)

            if info["type"].startswith("geo") or info["name"] == "latitude":
                has_geo_fields = True

            if info["type"] == "repeat":
                if name in nested_field_dict:
                    conf = nested_field_dict[name]
                    for key, val in info.items():
                        if key in ("type", "children"):
                            conf[key] = val
                        else:
                            conf.setdefault(key, val)
                else:
                    nested_fields.append(info)
                    nested_field_dict[name] = info
            else:
                fields.append(info)

        config = getattr(self.Meta, "wq_config", {}).copy()
        config.update(getattr(self, "wq_config", {}))
        config["form"] = fields + nested_fields

        meta = self.Meta.model._meta
        config.setdefault("name", meta.model_name)
        config.setdefault("verbose_name", meta.verbose_name)
        config.setdefault("verbose_name_plural", meta.verbose_name_plural)
        if meta.ordering:
            config.setdefault("ordering", meta.ordering)

        if has_geo_fields:
            config.setdefault("map", True)

        label_template = getattr(self.Meta.model, "wq_label_template", None)
        if label_template:
            config.setdefault("label_template", label_template)
        return config

    def get_wq_field_info(self, name, field, model=None):
        if isinstance(field, NaturalKeySerializer):
            children = [
                self.get_wq_field_info(n, f, model=field.Meta.model)
                for n, f in field.get_fields().items()
            ]
            if len(children) == 1:
                info = children[0]
                info["name"] = name + "[%s]" % info["name"]

                fk = self.get_wq_foreignkey_info(field.Meta.model)
                if fk:
                    info["wq:ForeignKey"] = fk
                    info["type"] = "select one"
            else:
                info = {
                    "name": name,
                    "type": "group",
                    "bind": {"required": True},
                    "children": children,
                }
            info["label"] = field.label or name.replace("_", " ").title()
            return info

        info = {
            "name": name,
            "label": field.label or name.replace("_", " ").title(),
        }
        if field.required:
            info.setdefault("bind", {})
            info["bind"]["required"] = True

        if field.help_text:
            info["hint"] = field.help_text

        if isinstance(field, serializers.ChoiceField):
            info["choices"] = get_choice_list(field.grouped_choices)
        elif getattr(field, "max_length", None):
            if not isinstance(field, serializers.FileField):
                info["wq:length"] = field.max_length

        if isinstance(field, serializers.BaseSerializer):
            # Nested model with a foreign key to this one
            if isinstance(field, serializers.ListSerializer):
                info["type"] = "repeat"
                serializer = field.child
            else:
                info["type"] = "group"
                serializer = field

            serializer.context["router"] = self.router
            if hasattr(serializer, "get_wq_config"):
                child_config = serializer.get_wq_config()
            else:
                child_config = {"form": []}

            for key in child_config:
                if key in (
                    "name",
                    "verbose_name",
                    "verbose_name_plural",
                    "url",
                    "postsave",
                    "label_template",
                ):
                    continue
                elif key == "form":
                    info_key = "children"
                else:
                    info_key = key
                info[info_key] = child_config[key]

        elif isinstance(field, serializers.RelatedField):
            # Foreign key to a parent model
            info["type"] = "select one"
            info["name"] = info["name"].replace("_id", "")
            info["label"] = info["label"].replace(" Id", "")
            if hasattr(field, "queryset"):
                fk = self.get_wq_foreignkey_info(field.queryset.model)
                if fk:
                    model = model or self.Meta.model
                    source = model._meta.get_field(name)
                    info["wq:ForeignKey"] = fk
                    info[
                        "wq:related_name"
                    ] = source.remote_field.get_accessor_name()

        elif isinstance(field, serializers.ManyRelatedField):
            # ManyToMany field to related model
            info["type"] = "select"
            info["name"] = info["name"].replace("_id", "")
            info["label"] = info["label"].replace(" Id", "")
            if field.child_relation.queryset:
                fk = self.get_wq_foreignkey_info(
                    field.child_relation.queryset.model
                )
                info["wq:ForeignKey"] = fk

        if "type" not in info:
            info["type"] = "string"

            for field_type, xlsform_type in self.xlsform_types.items():
                if isinstance(field, field_type):
                    info["type"] = xlsform_type
                    break

            if info["type"] == "geoshape":
                model = model or self.Meta.model
                source = model._meta.get_field(name)
                if info["type"] == "geoshape":
                    geom_type = getattr(source, "geom_type", None)
                    if geom_type == "POINT":
                        info["type"] = "geopoint"
                    elif geom_type == "LINESTRING":
                        info["type"] = "geotrace"

            if info["type"] == "string":
                model = model or self.Meta.model
                try:
                    source = model._meta.get_field(name)
                except FieldDoesNotExist:
                    pass
                else:
                    if source.get_internal_type() == "TextField":
                        info["type"] = "text"

        if "wq_config" in field.style:
            info.update(field.style["wq_config"])

        field_config = getattr(self.Meta, "wq_field_config", {})
        if name in field_config:
            info.update(field_config[name])

        return info

    def get_wq_foreignkey_info(self, model):
        if not self.router or not self.router.model_is_registered(model):
            return None
        else:
            serializer = self.router.get_serializer_for_model(model)
            model_conf = serializer().get_wq_config()
            return model_conf["name"]

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if getattr(self.Meta, "wq_fieldsets", None):
            return self.to_virtual_fieldsets(data)
        else:
            return data

    def to_virtual_fieldsets(self, data):
        for name, conf in self.Meta.wq_fieldsets.items():
            if name == "":
                continue
            for field in conf.get("fields") or []:
                if field in self.id_fields:
                    field = f"{field}_id"
                if field not in data:
                    continue
                data.setdefault(name, {})
                data[name][field] = data.pop(field)
        return data

    def to_internal_value(self, data):
        if not data or not getattr(self.Meta, "wq_fieldsets", None):
            return super().to_internal_value(data)

        for name, conf in self.Meta.wq_fieldsets.items():
            if name == "" or not conf.get("fields"):
                continue
            fs_data = data.pop(name, None)
            if isinstance(fs_data, dict):
                data.update(fs_data)

        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            if isinstance(e.detail, dict):
                raise serializers.ValidationError(
                    self.to_virtual_fieldsets(e.detail)
                )
            else:
                raise

    @property
    def router(self):
        if "view" not in self.context and "router" not in self.context:
            return None
        if "view" in self.context:
            return self.context["view"].router
        else:
            return self.context["router"]

    @property
    def is_detail(self):
        if getattr(self.Meta, "depth", 0) > 0:
            return True
        view = self.context.get("view", None)
        return view and view.action != "list"

    @property
    def is_edit(self):
        view = self.context.get("view", None)
        return view and view.action == "edit"

    @property
    def is_geojson(self):
        request = self.context.get("request", None)
        if not request:
            return
        if request.accepted_renderer.format == "geojson":
            return True
        return False

    @property
    def is_html(self):
        request = self.context.get("request", None)
        if not request:
            return
        if request.accepted_renderer.format == "html":
            return True
        return False

    @property
    def is_config(self):
        return getattr(self, "_for_wq_config", False)

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        fields = self.update_id_fields(fields)
        fields.update(self.get_label_fields(fields))
        fields.update(self.get_nested_arrays(fields))

        exclude = set()

        def get_exclude(meta_name):
            return set(getattr(self.Meta, meta_name, []))

        if not self.is_detail and not self.is_config:
            exclude |= get_exclude("list_exclude")
            if self.is_html:
                exclude |= get_exclude("html_list_exclude")

        if self.is_config:
            exclude |= get_exclude("config_exclude")

        if not self.is_config and not self.is_geojson:
            defer_geometry = getattr(self.Meta, "wq_config", {}).get(
                "defer_geometry", False
            )
            if defer_geometry:
                for field_name, field in fields.items():
                    if isinstance(field, GeometryField):
                        exclude.add(field_name)

        for field_name in list(exclude):
            fields.pop(field_name, None)

        return fields

    def update_id_fields(self, fields):
        if "id" not in self._declared_fields:
            lookup = getattr(self.Meta, "wq_config", {}).get("lookup", None)
            if lookup and lookup != "id":
                fields["id"] = serializers.ReadOnlyField(source=lookup)

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
            auto_related_field = (
                serializers.BaseSerializer,
                serializers.ManyRelatedField,
                serializers.SlugRelatedField,
            )
            if not isinstance(default_field, auto_related_field):
                continue
            if isinstance(default_field, NaturalKeySerializer):
                continue

            if name + "_id" not in fields:
                id_field, id_field_kwargs = self.build_relational_field(
                    name, field
                )
                extra_field_kwargs = extra_kwargs.get(name, {})
                extra_field_kwargs.update(extra_kwargs.get(name + "_id", {}))
                self.include_extra_kwargs(
                    id_field_kwargs,
                    extra_field_kwargs,
                )
                id_field_kwargs["source"] = name
                id_fields[name] = id_field(**id_field_kwargs)

            if name in fields:
                # Update/remove DRF default foreign key field (w/o _id)
                if self.is_detail and isinstance(
                    default_field, serializers.BaseSerializer
                ):
                    # Nested representation, keep for detail template context
                    fields[name].read_only = True
                else:
                    # Otherwise we don't need this field
                    del fields[name]

        if not id_fields:
            return fields

        self.id_fields.update(id_fields)

        # Ensure _id fields show up in the same order they appear on model
        updated_fields = OrderedDict()
        for field in self.Meta.model._meta.fields:
            name = field.name
            if name in fields:
                updated_fields[name] = fields.pop(name)
            if name in id_fields:
                updated_fields[name + "_id"] = id_fields.pop(name)

        if fields:
            updated_fields.update(fields)

        if id_fields:
            for name in id_fields:
                updated_fields[name + "_id"] = id_fields[name]

        return updated_fields

    def get_label_fields(self, default_fields):
        if not self.add_label_fields:
            return {}
        fields = {}

        exclude = getattr(self.Meta, "exclude", [])
        if "label" not in exclude and "label" not in default_fields:
            fields["label"] = serializers.ReadOnlyField(source="__str__")

        info = model_meta.get_field_info(self.Meta.model)

        # Add labels for dates and fields with choices
        for name, field in info.fields.items():
            if name in getattr(self.Meta, "exclude", []):
                continue
            if name + "_label" in default_fields:
                continue
            if isinstance(field, model_fields.DateTimeField):
                fields[name + "_label"] = LocalDateTimeField(source=name)
            if field.choices:
                fields[name + "_label"] = serializers.ReadOnlyField(
                    source="get_%s_display" % name
                )
            if isinstance(field, MODEL_BOOLEAN_FIELDS):
                fields[name + "_label"] = BooleanLabelField(
                    source=name,
                )

        return fields

    def get_nested_arrays(self, fields):
        model_class = self.Meta.model
        nested = {}
        for array_model in getattr(self.Meta, "wq_nested_arrays", None) or []:
            fk_field = None
            for field in array_model._meta.fields:
                if field.related_model == model_class:
                    fk_field = field
                    break
            fk_desc = (
                f"ForeignKey from {array_model.__name__}"
                f" to {model_class.__name__}"
            )
            if not fk_field:
                raise ImproperlyConfigured(f"No {fk_desc}")

            rel_name = fk_field.remote_field.related_name
            if not rel_name or rel_name.startswith("+"):
                raise ImproperlyConfigured(f"No related_name for {fk_desc}")

            if rel_name in fields:
                continue

            base = self.get_nested_array_serializer(array_model)
            base_fields = getattr(base.Meta, "fields", None) or []
            base_exclude = getattr(base.Meta, "exclude", None) or []

            class NestedSerializer(base):
                class Meta(base.Meta):
                    model = array_model
                    if not base_fields or base_fields == "__all__":
                        fields = None
                        if fk_field.name not in base_exclude:
                            exclude = [*base_exclude, fk_field.name]
                    else:
                        fields = [f for f in base_fields if f != fk_field.name]

            nested[rel_name] = NestedSerializer(many=True)
        return nested

    def get_nested_array_serializer(self, array_model):
        if self.router:
            return self.router._serializers.get(array_model, ModelSerializer)
        else:
            return ModelSerializer

    @classmethod
    def for_model(
        cls,
        model_class,
        include_fields=None,
        nested_arrays=None,
        serializer_depth=None,
    ):
        class Serializer(cls):
            class Meta(getattr(cls, "Meta", object)):
                model = model_class
                if include_fields:
                    fields = include_fields
                if nested_arrays:
                    wq_nested_arrays = nested_arrays
                if serializer_depth is not None:
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
        if field_class == LookupRelatedField:
            field_kwargs["router"] = self.router
            field_kwargs["model"] = relation_info.related_model
        return field_class, field_kwargs

    def build_nested_field(self, field_name, relation_info, nested_depth):
        field_class, field_kwargs = super(
            ModelSerializer, self
        ).build_nested_field(field_name, relation_info, nested_depth)
        field_kwargs["required"] = False
        if self.router and not issubclass(field_class, NaturalKeySerializer):
            field_class = self.router.get_serializer_for_model(
                relation_info.related_model, nested_depth
            )
        return field_class, field_kwargs

    class Meta:
        wq_config = {}
        wq_field_config = {}
        wq_fieldsets = None
        wq_nested_arrays = None
        list_serializer_class = ListSerializer
