from rest_framework import generics, status, response, mixins

from django.contrib.contenttypes.models import ContentType
from wq.db.patterns.models import (Annotation, AnnotatedModel, AnnotationType,
                                   Identifier, IdentifiedModel, RelatedModel)
from wq.db.rest import util

RESERVED_PARAMETERS = ('_', 'page', 'limit', 'format')
_FORBIDDEN_RESPONSE = "Sorry %s, you do not have permission to %s this %s."

class View(generics.GenericAPIView):
    def get_template_names(self):
        if (getattr(self, 'resource', None) is None 
              or getattr(self.resource, 'model') is None):
            template = type(self).__name__.replace('View', '').lower()
        else:
            model = getattr(self, 'model', self.resource.model)
            ctid   = util.get_id(util.get_ct(model))
            if self._suffix == 'List':
                template = ctid + '_list'
            else:
                template = ctid + '_detail'
        return (template,)

class InstanceModelView(View, views.RetrieveUpdateDestroyAPIView):
    def get_instance(self, *args, **kwargs):
        if issubclass(self.resource.model, IdentifiedModel):
            return self.resource.model.objects.get_by_identifier(kwargs['pk'])
        else:
            return super(InstanceModelView, self).get_instance(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not util.has_perm(request.user, ct, 'view'):
            forbid(request.user, ct, 'view')
        return super(InstanceModelView, self).get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not util.has_perm(request.user, ct, 'change'):
            forbid(request.user, ct, 'change')

        res = super(InstanceModelView, self).put(request, *args, **kwargs)

        if issubclass(self.resource.model, AnnotatedModel):
            atypes = AnnotationType.objects.filter(contenttype=ct)
            for at in atypes:
                fname = 'annotation-%s' % at.pk
                if fname in self.CONTENT:
                    annot, isnew = Annotation.objects.get_or_create(
                        type=at, content_type=ct, object_id=res.pk)
                    annot.value = self.CONTENT[fname]
                    annot.save()
        return res

    def delete(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not util.has_perm(request.user, ct, 'delete'):
            forbid(request.user, ct, 'delete')
        return super(InstanceModelView, delete).put(request, *args, **kwargs)

class ListOrCreateModelView(View, views.ListCreateAPIView):
    annotations = None 
    parent = None
    def get_query_kwargs(self, *args, **kwargs):
        for key, val in self.request.GET.items():
            if key in RESERVED_PARAMETERS:
                continue
            kwargs[key] = val if isinstance(val, unicode) else val[0]

        ctype = util.get_ct(self.resource.model)
        for key, val in kwargs.items():
            if key in ('target',):
                del kwargs[key]
                continue
            found = False
            for f in self.resource.model._meta.fields:
                if f.name != key and util.get_id(ctype) + f.name != key:
                    continue
                found = True
                if getattr(f, 'rel', None):
                    del kwargs[key]
                    if issubclass(f.rel.to, IdentifiedModel):
                        kwargs[f.name] = f.rel.to.objects.get_by_identifier(val)
                    else:
                        kwargs[f.name] = f.rel.to.objects.get(pk=val)
                    self.parent = kwargs[f.name]

            if not found and issubclass(self.resource.model, RelatedModel):
                for pct in util.get_all_parents(ctype):
                    if util.get_id(pct) == key:
                        pclass = pct.model_class()
                        if issubclass(pclass, IdentifiedModel):
                            self.parent = pclass.objects.get_by_identifier(kwargs[key])
                        else:
                            self.parent = pclass.objects.get(pk=kwargs[key])
                        del kwargs[key]
                        objs = self.resource.model.objects.filter_by_related(self.parent)
                        kwargs['pk__in'] = objs.values_list('pk', flat=True)
                
        kwargs = super(ListOrCreateModelView, self).get_query_kwargs(*args, **kwargs)
        return kwargs

    @property
    def CONTENT(self):
        content = super(ListOrCreateModelView, self).CONTENT
        if issubclass(self.resource.model, AnnotatedModel):
            ct = ContentType.objects.get_for_model(self.resource.model)
            atypes = AnnotationType.objects.filter(contenttype=ct)
            self.annotations = {}
            for at in atypes:
                fname = 'annotation-%s' % at.pk
                if fname in content:
                    self.annotations[at] = content[fname]
                    del content[fname]
        return content

    def get(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not util.has_perm(request.user, ct, 'view'):
            forbid(request.user, ct, 'view')
        return super(ListOrCreateModelView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not util.has_perm(request.user, ct, 'add'):
            forbid(request.user, ct, 'add')
        res = super(ListOrCreateModelView, self).post(request, *args, **kwargs)

        if issubclass(self.resource.model, AnnotatedModel):
            for at, val in self.annotations.iteritems():
                annot, isnew = Annotation.objects.get_or_create(
                type=at, content_type=ct, object_id=res.raw_content.id)
                annot.value = val
                annot.save()
        return res

    def filter_response(self, obj):
        result = super(ListOrCreateModelView, self).filter_response(obj)
        if 'results' not in result:
            return result
        result['list'] = result['results']
        if 'list' in obj and 'pages' in obj:
            result['multiple'] = obj['pages'] > 1
        del result['results']
        if 'target' in self.kwargs:
            result['target'] = self.kwargs['target']
        if getattr(self, 'parent', None):
            result['parent_label'] = unicode(self.parent)
            result['parent_id']    = util.get_object_id(self.parent)
            result['parent_url']   = '%s/%s' % (
                util.geturlbase(util.get_ct(self.parent)), util.get_object_id(self.parent)
            )
        return result

def forbid(user, ct, perm):
    raise response.ErrorResponse(status.HTTP_403_FORBIDDEN, {
        'errors': [_FORBIDDEN_RESPONSE % (user, perm, ct)]
    })
