from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response
from .models import get_ct, get_object_id

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
    parent = None

    @property
    def template_name(self):
        return get_ct(self.model).identifier + '_list.html'

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
