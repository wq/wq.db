from djangorestframework.resources import ModelResource as RestModelResource

from django.contrib.gis.db.models.fields import GeometryField

from django.contrib.contenttypes.models import ContentType
from wq.db.identify.models import IdentifiedModel
from wq.db.annotate.models import Annotation, AnnotatedModel, AnnotationType

from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

from wq.db.rest.util import get_ct, get_id, get_object_id, geturlbase

_resource_map = {}
_context_mixin_map = {}

class ModelResource(RestModelResource):
    @property
    def full_context(self):
        return getattr(self.view, '_suffix', None) != 'List'

    def get_fields(self, obj):
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

        if (self.full_context):
            for mixin in _context_mixin_map.values():
                if mixin.valid_for_model(self.model):
                    fields.append(mixin.name)

        return fields

    def updates(self, instance):
        ct = ContentType.objects.get_for_model(instance)
        idname = get_id(ct) + '_id'
        annots = Annotation.objects.filter(content_type=ct, object_id=instance.pk)
        updates = []
        for a in annots:
            updates.append({'id': a.pk,
                            'annotationtype_id': a.type.pk,
                            idname:    instance.pk,
                            'value':   a.value})
        return {'annotation': updates}

    def validate_request(self, data, files=None):
        extra_fields = ()
        if issubclass(self.model, AnnotatedModel):
            ct = ContentType.objects.get_for_model(self.model)
            atypes = AnnotationType.objects.filter(contenttype=ct)
            extra_fields = ('annotation-%s' % at.pk for at in atypes)
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
                if mixin.valid_for_model(self.model):
                    data[mixin.name] = mixin.get_data(instance)
        return data

class ContextMixin(object):
    model = None
    target_model = None

    @property
    def name(self):
        return geturlbase(get_ct(self.model))

    def get_data(self, instance):
        raise NotImplementedError

    def valid_for_model(self, model):
        return issubclass(model, self.target_model)

def register(model_class, resource_class):
    _resource_map[model_class] = resource_class

def register_context_mixin(cls):
    mixin = cls()
    _context_mixin_map[mixin.name] = mixin

def get_for_model(model_class):
    if model_class in _resource_map:
        return _resource_map[model_class]
    else:
        return type(model_class.__name__ + "Resource", (ModelResource,),
                    {'model': model_class})

def autodiscover():
    for app_name in settings.INSTALLED_APPS:
        app = import_module(app_name)
        if module_has_submodule(app, 'resources'):
            import_module(app_name + '.resources')
