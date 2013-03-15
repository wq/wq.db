from rest_framework.serializers import ModelSerializer as RestModelSerializer
from rest_framework.serializers import Field, WritableField, RelatedField, PrimaryKeyRelatedField
from rest_framework.pagination import PaginationSerializer as RestPaginationSerializer

from django.contrib.gis.db.models.fields import GeometryField as GISGeometryField

from wq.db.patterns.models import Annotation, AnnotationType

from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

from wq.db.rest.models import ContentType, get_ct, get_object_id

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
    def field_to_native(self, obj, field_name):
        if field_name.endswith('_id'):
            field_name = field_name[:-3] 
        val = getattr(obj, self.source or field_name)
        if self.many:
            return [get_object_id(item) for item in val.all()]
        else:
            return get_object_id(val)

class ModelSerializer(RestModelSerializer):
    def __init__(self, *args, **kwargs):
        self.field_mapping[GISGeometryField] = GeometryField
        super(ModelSerializer, self).__init__(*args, **kwargs)

    def get_default_fields(self, *args, **kwargs):
        fields = super(ModelSerializer, self).get_default_fields(*args, **kwargs)
        fields['id'] = IDField()
        fields['label'] = Field(source='__unicode__')
        if 'view' not in self.context:
            return fields

        # TODO:
        # if (getattr(self.view, "method", None) in ("PUT", "POST")):
        #     fields.append(UpdatesField)
        
        router = self.context['view'].router

        many = self.many or self.source == 'object_list'

        # Special handling for related fields
        for name, field in fields.items():
            if not isinstance(field, PrimaryKeyRelatedField):
                continue

            # Move [fieldname] to [fieldname]_id, and add [fieldname]_label

            if many:
                # In list views, remove [fieldname] as an attribute
                # (it's up to a client like app.js to resolve [fieldname] to use
                # [fieldname]_id to resolve [fieldname] to an actual object)
                del fields[name]
            else:
                # In detail views, make [fieldname] a nested field
                model_field, model, direct, m2m = self.opts.model._meta.get_field_by_name(name)
                fields[name] = self.get_nested_field(model_field)

            # Stop processing if this is a many-to-many-field
            if field.many:
                continue

            # Add _id and _label to context
            fields[name + '_id'] = IDRelatedField(queryset=field.queryset)
            fields[name + '_label'] = LabelRelatedField(queryset=field.queryset)
                
        # Add child objects (serialize with registered serializers)
        ct = get_ct(self.opts.model)
        for cct, rel in ct.get_children(include_rels=True):
            accessor = rel.get_accessor_name()
            if accessor == rel.field.related_query_name():
                fields[accessor] = router.get_serializer_for_model(cct.model_class())()

        return fields

    def get_nested_field(self, model_field):
        model = model_field.rel.to
        if 'view' in self.context and hasattr(self.context['view'], 'router'):
            router = self.context['view'].router
            return router.get_serializer_for_model(model)()
        return super(ModelSerializer, self).get_nested_field(self, model_field)

    #TODO: make this a field
    def updates(self, instance):
        ct = get_ct(instance)
        idname = ct.identifier + '_id'
        res = get_for_model(Annotation)
        qs = getattr(res, 'queryset', Annotation.objects)
        annots = qs.filter(content_type=ct, object_id=instance.pk)
        updates = []
        updates = map(res().serialize_model, annots)
        return {'annotation': updates}

    #TODO: update & test
    def validate_request(self, data, files=None):
        extra_fields = self._property_fields_set
        ct = get_ct(self.model)
        if ct.is_annotated:
            atypes = AnnotationType.objects.filter(contenttype=ct)
            extra_fields.update(('annotation-%s' % at.pk for at in atypes))
        data = self._validate(data, files, extra_fields)
        return data

class PaginationSerializer(RestPaginationSerializer):
    results_field = 'list'
    pages = Field('paginator.num_pages')
    def to_native(self, obj):
        result = super(PaginationSerializer, self).to_native(obj)
        result['multiple'] = result['pages'] > 1
        return result
