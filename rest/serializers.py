from rest_framework.serializers import ModelSerializer as RestModelSerializer
from rest_framework.serializers import Field, WritableField, RelatedField, PrimaryKeyRelatedField
from rest_framework.pagination import PaginationSerializer as RestPaginationSerializer

from django.contrib.gis.db.models.fields import GeometryField as GISGeometryField

from django.conf import settings

from .models import DjangoContentType, ContentType, get_ct, get_object_id, get_by_identifier

class GeometryField(WritableField):
    def to_native(self, value):
        import json
        return json.loads(value.geojson)

class LabelRelatedField(RelatedField):
    def field_to_native(self, obj, field_name):
        if field_name.endswith('_label'):
            field_name = field_name[:-6] 
        val = getattr(obj, self.source or field_name)
        if self.many:
            return [unicode(item) for item in val.all()]
        else:
            return unicode(val)

class IDField(Field):
    def field_to_native(self, obj, field_name):
        return get_object_id(obj)

#TODO: investigate use of SlugRelatedField and/or PrimaryKeyRelatedField
class IDRelatedField(RelatedField):
    read_only = False
    def field_to_native(self, obj, field_name):
        if field_name.endswith('_id'):
            field_name = field_name[:-3] 
        val = getattr(obj, self.source or field_name)
        if val is None:
            return None
        if self.many:
            return [get_object_id(item) for item in val.all()]
        else:
            return get_object_id(val)

    def field_from_native(self, data, files, field_name, into):
        if field_name.endswith('_id'):
            field_name = field_name[:-3] 
        return super(IDRelatedField, self).field_from_native(data, files, field_name, into)

    def from_native(self, data):
        return get_by_identifier(self.queryset, data)

class ContentTypeField(RelatedField):
    read_only = False
    def to_native(self, obj):
        return obj.name

    def from_native(self, data, files):
        return ContentType.objects.get(name=data)

class ModelSerializer(RestModelSerializer):
    def __init__(self, *args, **kwargs):
        self.field_mapping[GISGeometryField] = GeometryField
        super(ModelSerializer, self).__init__(*args, **kwargs)

    def get_default_fields(self, *args, **kwargs):
        fields = super(ModelSerializer, self).get_default_fields(*args, **kwargs)
        fields['id'] = IDField()
        fields['label'] = Field(source='__unicode__')
        if 'view' not in self.context and 'router' not in self.context:
            return fields

        if 'view' in self.context:
            router = self.context['view'].router
        else:
            router = self.context['router']
        many = self.many or self.source == 'object_list'
        if 'request' in self.context and self.context['request'].method != 'GET':
            saving = True
        else:
            saving = self.context.get('saving', False)

        # Special handling for related fields
        for name, field in fields.items():
            if not isinstance(field, PrimaryKeyRelatedField):
                continue

            model_field, model, direct, m2m = self.opts.model._meta.get_field_by_name(name)

            if model_field.rel.to == DjangoContentType:
                fields['for'] = ContentTypeField(source=name, queryset=field.queryset)
                del fields[name]
                continue

            if many or (saving and not m2m):
                # In list views, remove [fieldname] as an attribute in favor of
                # [fieldname]_id and [fieldname]_label (below).
                # (Except when saving m2m items, in which case we need the nested field)
                del fields[name]
            else:
                # In detail views, always make [fieldname] a nested field. This
                # is needed to generate renderer contexts to support deep linking.
                # (The list view doesn't need the full object, as REST clients
                #  like wq.app's app.js can use preloaded lists and callbacks 
                #  to resolve [fieldname] to an object, given [fieldname]_id.)
                fields[name] = self.get_nested_field(model_field)

            # Stop processing if this is a many-to-many-field
            if field.many or m2m:
                continue

            # Add _id and _label to context
            fields[name + '_id'] = IDRelatedField(
                source   = name,
                queryset = field.queryset,
                required = field.required
            )
            fields[name + '_label'] = LabelRelatedField(queryset=field.queryset)
                
        # Add child objects (serialize with registered serializers)
        if not router:
            return fields

        ct = get_ct(self.opts.model)
        for cct, rel in ct.get_children(include_rels=True):
            accessor = rel.get_accessor_name()
            if accessor == rel.field.related_query_name():
                cls = router.get_serializer_for_model(cct.model_class())
                if self.opts.depth > 1:
                    serializer = cls(context=self.context)
                else:
                    serializer = cls()
                fields[accessor] = serializer

        return fields

    def get_nested_field(self, model_field):
        model = model_field.rel.to
        if 'view' in self.context and hasattr(self.context['view'], 'router'):
            router = self.context['view'].router
            return router.get_serializer_for_model(model)()
        return super(ModelSerializer, self).get_nested_field(model_field)

    # Any IDRelatedField errors should be reported without the '_id' suffix
    # FIXME: is there a better way to fix this?
    @property
    def errors(self):
        errors = super(ModelSerializer, self).errors
        for field_name in self.fields:
            if field_name not in errors or not field_name.endswith('_id'):
                continue
            if not type(self.fields[field_name]) == IDRelatedField:
                continue
            field_name = field_name[:-3]
            errors[field_name] = errors[field_name + '_id']
            del errors[field_name + '_id']
        return errors


class PaginationSerializer(RestPaginationSerializer):
    results_field = 'list'
    page = Field('number')
    pages = Field('paginator.num_pages')
    per_page = Field('paginator.per_page')
    def to_native(self, obj):
        result = super(PaginationSerializer, self).to_native(obj)
        result['multiple'] = result['pages'] > 1
        return result
