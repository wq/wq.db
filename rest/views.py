from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from .models import get_ct, get_object_id, get_by_identifier
from django.conf import settings

from .caching import jc_backend, MIDDLEWARE_SECONDS


class View(generics.GenericAPIView):
    router = None
    cached = False
    depth = 0
    ignore_kwargs = []

    @property
    def template_name(self):
        return type(self).__name__.replace('View', '').lower() + '.html'

    @property
    def cached_models(self):
        if not getattr(self, 'model', None):
            return []
        ct = get_ct(self.model)
        ctypes = [ct]
        ctypes += [pct for pct in ct.get_all_parents()]
        ctypes += [cct for cct in ct.get_all_children()]
        return [ctype.model_class() for ctype in ctypes]

    def can_cache(self, request):
        if jc_backend and self.cached and request.method.lower() == 'get':
            return True
        return False

    def get_cache_key(self, request):
        def resolve_table(model):
            return model._meta.db_table
        tables = map(resolve_table, self.cached_models)
        genkey = jc_backend.keyhandler.get_generation(*tables)

        pathkey = jc_backend.keyhandler.keygen.gen_key(
            request.path,
            request.META.get('QUERY_STRING', "")
        )
        return "%s_wq_view_%s.%s" % (
            jc_backend.keyhandler.prefix, genkey, pathkey
        )

    def get_cached(self, request):
        if not self.can_cache(request):
            return None
        data = jc_backend.cache_backend.get(self.get_cache_key(request))
        if isinstance(data, dict):
            data['from_cache'] = True
        return data

    def set_cached(self, request, data):
        jc_backend.cache_backend.set(
            self.get_cache_key(request),
            data,
            MIDDLEWARE_SECONDS
        )

    def dispatch(self, request, *args, **kwargs):
        if self.get_cached(request):
            request = self.initialize_request(request, *args, **kwargs)
            self.request = request
            self.args = args
            self.kwargs = kwargs
            self.headers = self.default_response_headers
            self.initial(request, *args, **kwargs)
            response = Response(self.get_cached(request))
            self.response = self.finalize_response(
                request, response, *args, **kwargs
            )
        else:
            response = super(View, self).dispatch(request, *args, **kwargs)
            if self.can_cache(request):
                self.set_cached(request, response.data)
        return response

    def get_template_names(self):
        return [self.template_name]

    def get_queryset(self):
        if self.router is not None and self.model is not None:
            return self.router.get_queryset_for_model(self.model)
        return super(View, self).get_queryset()

    def get_serializer_class(self):
        if self.router is not None and self.model is not None:
            return self.router.get_serializer_for_model(self.model, self.depth)
        return super(View, self).get_serializer_class()

    def get_paginate_by(self, queryset):
        renderer = self.request.accepted_renderer
        if getattr(renderer, 'disable_pagination', False):
            return None
        if self.router is not None and self.model is not None:
            return self.router.get_paginate_by_for_model(self.model)
        return super(View, self).get_paginate_by(queryset)

    def perform_content_negotiation(self, request, force=False):
        renderer, media_type = super(View, self).perform_content_negotiation(
            request, force
        )
        if media_type.startswith('text'):
            media_type += "; charset=%s" % (settings.DEFAULT_CHARSET)
        return renderer, media_type


class SimpleView(View):
    def get(self, request, *args, **kwargs):
        return Response({})


class InstanceModelView(View, generics.RetrieveUpdateDestroyAPIView):
    cached = True
    depth = 1

    @property
    def template_name(self):
        if self.kwargs.get('mode', False) in ('edit', 'new'):
            return get_ct(self.model).identifier + '_edit.html'
        else:
            return get_ct(self.model).identifier + '_detail.html'

    def get_slug_field(self):
        if get_ct(self.model).is_identified:
            return 'primary_identifiers__slug'
        else:
            return 'pk'

    def get_object(self, queryset=None):
        if self.kwargs.get('mode', False) == "new":
            return self.model()

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
    cached = True
    depth = 0

    @property
    def template_name(self):
        return get_ct(self.model).identifier + '_list.html'

    def list(self, request, *args, **kwargs):
        response = super(ListOrCreateModelView, self).list(
            request, *args, **kwargs
        )
        if not isinstance(response.data, dict):
            return response

        if 'target' in self.kwargs:
            response.data['target'] = self.kwargs['target']
        ct = get_ct(self.model)
        for pct in get_ct(self.model).get_all_parents():
            self.get_parent(pct, response)
        return response

    def create(self, request, *args, **kwargs):
        response = super(ListOrCreateModelView, self).create(
            request, *args, **kwargs
        )
        if not request.accepted_media_type.startswith('text/html'):
            return response

        # text/html probably means a form post from an older browser
        if response.status_code == status.HTTP_201_CREATED:
            ct = get_ct(self.model)
            oid = response.data['id']
            url = '/%s/%s' % (ct.urlbase, oid)
            return Response(
                {'detail': 'Created'},
                status=status.HTTP_302_FOUND,
                headers={'Location': url}
            )
        else:
            errors = [{
                'field': key,
                'errors': val
            } for key, val in response.data.items()]
            template = get_ct(self.model).identifier + '_error.html'
            return Response(
                {
                    'errors': errors,
                    'post': request.DATA
                },
                status=response.status_code,
                template_name=template
            )

    def get_parent(self, ct, response):
        pid = self.kwargs.get(ct.identifier, None)
        if not pid:
            return

        pcls = ct.model_class()
        if (self.router and pcls in self.router._views
                and self.router._views[pcls][1]):
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
        response.data['parent_id'] = objid
        response.data['parent_url'] = '%s%s' % (urlbase, objid)
        response.data['parent_is_' + ct.identifier] = True
        return parent
