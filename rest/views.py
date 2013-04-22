from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response
from .models import get_ct, get_object_id, get_by_identifier

class View(generics.GenericAPIView):
    router = None

    @property
    def template_name(self):
        return type(self).__name__.replace('View', '').lower() + '.html'

    def get_template_names(self):
        return [self.template_name]

    def get_queryset(self):
        if self.router is not None and self.model is not None:
            return self.router.get_queryset_for_model(self.model)
        return super(View, self).get_queryset()

    def get_serializer_class(self):
        if self.router is not None and self.model is not None:
            return self.router.get_serializer_for_model(self.model)
        return super(View, self).get_serializer_class()

class SimpleView(View):
    def get(self, request, *args, **kwargs):
        return Response({})

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

class ListOrCreateModelView(View, generics.ListCreateAPIView):
    @property
    def template_name(self):
        return get_ct(self.model).identifier + '_list.html'

    def list(self, request, *args, **kwargs):
        response = super(ListOrCreateModelView, self).list(request, args, kwargs)

        if 'target' in self.kwargs:
            response.data['target'] = self.kwargs['target']
        ct = get_ct(self.model)
        for pct in get_ct(self.model).get_all_parents():
            self.get_parent(pct, response)
        return response

    def get_parent(self, ct, response):
        pid = self.kwargs.get(ct.identifier, None)
        if not pid:
            return

        pcls = ct.model_class()
        if self.router and pcls in self.router._views:
            lv, dv = self.router._views[pcls]
            slug = dv().get_slug_field()
            parent = pcls.objects.get(**{slug: pid})
        else:
            parent = get_by_identifier(pcls.objects, pid)
        if ct.urlbase == '':
            urlbase = ''
        else:
            urlbase = ct.urlbase + '/'
        objid = get_object_id(parent)
        response.data['parent_label'] = unicode(parent)
        response.data['parent_id']    = objid
        response.data['parent_url']   = '%s%s' % (urlbase, objid)
