from django.http import Http404

from rest_framework import generics, status
from rest_framework.response import Response

from wq.db.patterns.models import Annotation, AnnotationType, Identifier

from .models import get_ct, get_object_id

RESERVED_PARAMETERS = ('_', 'page', 'limit', 'format')

class View(generics.GenericAPIView):
    router = None

    @property
    def template_name(self):
        return type(self).__name__.replace('View', '').lower() + '.html'

    def get_template_names(self):
        return [self.template_name]

    def get_serializer_class(self):
        if self.router is not None and self.model is not None:
            return self.router.get_serializer_for_model(self.model)
        return super(View, self).get_serializer_class()

class InstanceModelView(View, generics.RetrieveUpdateDestroyAPIView):
    @property
    def template_name(self):
        return get_ct(self.model).identifier + '_detail.html'

    def get_slug_field(self):
        if get_ct(self.model).is_identified:
            return 'primary_identifiers__slug'
        else:
            return 'pk'
    
    def get_object(self, queryset=None):
        try:
            obj = super(InstanceModelView, self).get_object(queryset)
        except Http404:
            if not get_ct(self.model).is_identified:
                raise

            # Allow retrieval via non-primary identifiers
            slug = self.kwargs.get(self.slug_url_kwarg)
            try:
                obj = self.model.objects.get_by_identifier(slug)
            except:
                raise Http404("Could not find %s with id '%s'" % (
                      self.model._meta.verbose_name,
                      slug
                ))
            #TODO: automatically redirect to primary identifier?
        return obj

    def update(self, request, *args, **kwargs):
        ct = get_ct(self.model)

        res = super(InstanceModelView, self).update(request, *args, **kwargs)

        # FIXME: test
        if ct.is_annotated:
            atypes = AnnotationType.objects.filter(contenttype=ct)
            for at in atypes:
                fname = 'annotation-%s' % at.pk
                if fname in self.CONTENT:
                    annot, isnew = Annotation.objects.get_or_create(
                        type=at, content_type=ct, object_id=res.pk)
                    annot.value = self.CONTENT[fname]
                    annot.save()
        return res

class ListOrCreateModelView(View, generics.ListCreateAPIView):
    parent = None

    @property
    def template_name(self):
        return get_ct(self.model).identifier + '_list.html'

    def get_query_kwargs_FIXME(self, *args, **kwargs):
        for key, val in self.request.GET.items():
            if key in RESERVED_PARAMETERS:
                continue
            kwargs[key] = val if isinstance(val, unicode) else val[0]

        ctype = get_ct(self.model)
        for key, val in kwargs.items():
            if key in ('target',):
                del kwargs[key]
                continue
            found = False
            for f in self.model._meta.fields:
                if f.name != key and ctype.identifier + f.name != key:
                    continue
                found = True
                if getattr(f, 'rel', None):
                    del kwargs[key]
                    if get_ct(f.rel.to).is_identified:
                        kwargs[f.name] = f.rel.to.objects.get_by_identifier(val)
                    else:
                        kwargs[f.name] = f.rel.to.objects.get(pk=val)
                    self.parent = kwargs[f.name]

            if not found and ctype.is_related:
                for pct in ctype.get_all_parents():
                    if pct.identifier == key:
                        pclass = pct.model_class()
                        if pct.is_identified:
                            self.parent = pclass.objects.get_by_identifier(kwargs[key])
                        else:
                            self.parent = pclass.objects.get(pk=kwargs[key])
                        del kwargs[key]
                        objs = self.model.objects.filter_by_related(self.parent)
                        kwargs['pk__in'] = objs.values_list('pk', flat=True)
                
        kwargs = super(ListOrCreateModelView, self).get_query_kwargs(*args, **kwargs)
        return kwargs

    def get_annotations(self, request):
        ct = get_ct(self.model)
        if not ct.is_annotated:
            return {}

        atypes = AnnotationType.objects.filter(contenttype=ct)
        annotations = {}
        for at in atypes:
            fname = 'annotation-%s' % at.pk
            if fname in request.DATA:
                annotations[at] = request.DATA[fname]
        return annotations

    def create(self, request, *args, **kwargs):
        res = super(ListOrCreateModelView, self).create(request, *args, **kwargs)

        ct = get_ct(self.model)
        if not ct.is_annotated:
            return res

        #FIXME: this should be handled by the annotation serializer
        for at, val in self.get_annotations(request).iteritems():
            annot, isnew = Annotation.objects.get_or_create(
                type = at,
                content_type = ct,
                object_id = self.object.id
            )
            annot.value = val
            annot.save()

        return res

    def filter_response_FIXME(self, obj):
        result = super(ListOrCreateModelView, self).filter_response(obj)
        if 'target' in self.kwargs:
            result['target'] = self.kwargs['target']
        if getattr(self, 'parent', None):
            result['parent_label'] = unicode(self.parent)
            result['parent_id']    = get_object_id(self.parent)
            result['parent_url']   = '%s/%s' % (
                get_ct(self.parent).urlbase, get_object_id(self.parent)
            )
        return result
