from rest_framework.serializers import ModelSerializer as RestModelSerializer

from django.contrib.gis.db.models.fields import GeometryField

from django.contrib.contenttypes.models import ContentType
from wq.db.patterns.models import Annotation, AnnotatedModel, AnnotationType

from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

from wq.db.rest.util import get_ct, get_id, get_object_id, geturlbase

class ModelSerializer(RestModelSerializer):
    @property
    def full_context(self):
        return not self.many

    def get_fields_FIXME(self, obj):
        fields = ['label']
        for f in self.model._meta.fields:
            if f.rel is None:
                fields.append(f.name)
            else:
                if type(f.rel).__name__ == 'OneToOneRel':
                    pass
                elif f.rel.to == ContentType:
                    fields.append('for')
                else:
                    fields.append(f.name + '_label')
                    fields.append(f.name + '_id')
        if (getattr(self.view, "method", None) in ("PUT", "POST")):
            fields.append("updates")

        return fields

    def get_nested_field(self, model_field):
        model = model_field.rel.to
        router = getattr(self.context, 'router', None):
        if router is not None:
            return router.get_serializer_for_model(model)
        return super(ModelSerializer, self).get_nested_field(self, model_field)

    def updates(self, instance):
        ct = ContentType.objects.get_for_model(instance)
        idname = get_id(ct) + '_id'
        res = get_for_model(Annotation)
        qs = getattr(res, 'queryset', Annotation.objects)
        annots = qs.filter(content_type=ct, object_id=instance.pk)
        updates = []
        updates = map(res().serialize_model, annots)
        return {'annotation': updates}

    def validate_request(self, data, files=None):
        extra_fields = self._property_fields_set
        if issubclass(self.model, AnnotatedModel):
            ct = ContentType.objects.get_for_model(self.model)
            atypes = AnnotationType.objects.filter(contenttype=ct)
            extra_fields.update(('annotation-%s' % at.pk for at in atypes))
        data = self._validate(data, files, extra_fields)
        return data

    def serialize_model(self, instance):
        data = super(ModelResource, self).serialize_model(instance)
        data['id']    = get_object_id(instance)
        data['label'] = unicode(instance)
        for f in self.model._meta.fields:
            if f.rel is not None:
                if f.rel.to == ContentType:
                    data['for'] = get_id(getattr(instance, f.name))
                else:
                    obj = getattr(instance, f.name)
                    if obj is None:
                        continue
                    data[f.name + '_id']    = get_object_id(obj)
                    data[f.name + '_label'] = unicode(obj)
            if isinstance(f, GeometryField):
                import json
                geo = getattr(instance, f.name)
                data[f.name] = json.loads(geo.geojson)

        if (self.full_context):
            for mixin in _context_mixin_map.values():
                if mixin.valid_for_model(type(instance)):
                    data[mixin.name] = mixin.get_data(instance)
        return data

