from django.http import Http404
from rest_framework.generics import GenericAPIView as RestGenericAPIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework import status, viewsets
from .models import get_ct, get_object_id, get_by_identifier


class GenericAPIView(RestGenericAPIView):
    router = None
    ignore_kwargs = []

    @property
    def template_name(self):
        """
        Infer template name from view/viewset name
        """
        name = type(self).__name__
        name = name.replace('ViewSet', '')
        name = name.replace('View', '')
        return name.lower() + '.html'

    @property
    def depth(self):
        return 0

    def get_template_names(self):
        return [self.template_name]

    def get_queryset(self):
        if self.router is not None and self.model is not None:
            return self.router.get_queryset_for_model(self.model, self.request)
        return super(GenericAPIView, self).get_queryset()

    def get_serializer_class(self):
        if self.router is not None and self.model is not None:
            return self.router.get_serializer_for_model(self.model, self.depth)
        return super(GenericAPIView, self).get_serializer_class()

    def get_paginate_by(self):
        if self.paginate_by_param not in self.request.GET:
            if self.router is not None and self.model is not None:
                return self.router.get_paginate_by_for_model(self.model)
        return super(GenericAPIView, self).get_paginate_by()


class SimpleView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response({})


class SimpleViewSet(viewsets.ViewSet, GenericAPIView):
    def list(self, request, *args, **kwargs):
        return Response({})


class ModelViewSet(viewsets.ModelViewSet, GenericAPIView):
    target = None

    @property
    def template_name(self):
        basename = get_ct(self.model).identifier
        if self.action in ('retrieve', 'create', 'update', 'delete'):
            suffix = 'detail'
        else:
            suffix = self.action
        return "%s_%s.html" % (basename, suffix)

    @property
    def depth(self):
        if self.action in ('retrieve', 'edit'):
            return 1
        else:
            return 0

    @detail_route()
    def edit(self, request, *args, **kwargs):
        """
        Generates a context appropriate for editing a form
        """
        response = self.retrieve(request, *args, **kwargs)
        self.add_lookups(response.data)
        return response

    def new(self, request):
        """
        new is a variant of the "edit" action, but with no existing model
        to lookup.
        """
        self.action = 'edit'
        init = request.GET.dict()
        for arg in self.ignore_kwargs:
            init.pop(arg, None)
        obj = self.model(**init)
        serializer = self.get_serializer(obj)
        data = serializer.data
        self.add_lookups(data)
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        """
        Custom retrieve watches for "new" lookup value and switches modes
        accordingly
        """
        if hasattr(self, 'lookup_url_kwarg'):
            # New in DRF 2.4?
            lookup = self.lookup_url_kwarg or self.lookup_field
        else:
            lookup = self.lookup_field

        if self.kwargs.get(lookup, "") == "new":
            # new/edit mode
            return self.new(request)
        else:
            # Normal detail view
            return super(ModelViewSet, self).retrieve(request, *args, **kwargs)

    def add_lookups(self, context):
        # Mimic _addLookups in wq.app/app.js
        context['edit'] = True
        ct = get_ct(self.model)
        for pct, fields in ct.get_foreign_keys().items():
            if not pct.is_registered():
                continue
            for field in fields:
                choices = self.get_lookup_choices(pct, context, field)
                self.set_selected(choices, context.get(field + '_id', ''))
                if field == pct.model:
                    context[pct.urlbase] = choices
                context[field + '_list'] = choices

    def set_selected(self, choices, value):
        for choice in choices:
            if choice['id'] == value:
                choice['selected'] = True

    def get_lookup_choices(self, ct, context, field_name=None):
        from wq.db import rest
        parent_model = ct.model_class()
        if not field_name:
            field_name = ct.model
        qs = rest.router.get_queryset_for_model(parent_model)
        fn = getattr(self, 'get_%s_choices' % field_name, None)
        if fn:
            qs = fn(qs, context)
        return rest.router.serialize(qs, many=True)

    def get_object(self):
        try:
            obj = super(ModelViewSet, self).get_object()
        except Http404:
            if not get_ct(self.model).is_identified:
                raise

            # Allow retrieval via non-primary identifiers
            slug = self.kwargs.get(self.lookup_url_kwarg)
            try:
                obj = self.model.objects.get_by_identifier(slug)
            except:
                raise Http404("Could not find %s with id '%s'" % (
                    self.model._meta.verbose_name,
                    slug
                ))
            # TODO: automatically redirect to primary identifier?
        return obj

    def list(self, request, *args, **kwargs):
        response = super(ModelViewSet, self).list(
            request, *args, **kwargs
        )
        if not isinstance(response.data, dict):
            return response

        if self.target:
            response.data['target'] = self.target
        ct = get_ct(self.model)
        for pct in ct.get_all_parents():
            self.get_parent(pct, response)
        return response

    def create(self, request, *args, **kwargs):
        response = super(ModelViewSet, self).create(
            request, *args, **kwargs
        )
        if not request.accepted_media_type.startswith('text/html'):
            # JSON request, assume client will handle redirect
            return response

        # HTML request, probably a form post from an older browser
        if response.status_code == status.HTTP_201_CREATED:
            return self.postsave(request, response)
        else:
            return self.saveerror(request, response)

    def postsave(self, request, response):
        ct = get_ct(self.model)
        conf = ct.get_config(request.user)

        # Redirect to new page
        postsave = conf.get('postsave', ct.identifier + '_detail')
        if '_' in postsave:
            page, mode = postsave.split('_')
        else:
            page = postsave
            mode = 'detail'

        oid = ""
        if page != ct.identifier:
            # Optional: return to detail view of a parent model
            ct = get_ct(page)
            if mode != "list":
                oid = response.data.get(page + '_id', None)
        else:
            # Default: return to detail view of the saved model
            if mode != "list":
                oid = response.data['id']

        if mode == "edit":
            oid += "/edit"
        url = '/%s/%s' % (ct.urlbase, oid)
        return Response(
            {'detail': 'Created'},
            status=status.HTTP_302_FOUND,
            headers={'Location': url}
        )

    def saverror(self, request, response):
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
        if self.router:
            slug = self.router.get_lookup_for_model(pcls)
            parent = pcls.objects.get(**{slug: pid})
        else:
            parent = get_by_identifier(pcls.objects, pid)
        if ct.urlbase == '':
            urlbase = ''
        else:
            urlbase = ct.urlbase + '/'
        objid = get_object_id(parent)
        response.data['parent_label'] = str(parent)
        response.data['parent_id'] = objid
        response.data['parent_url'] = '%s%s' % (urlbase, objid)
        response.data['parent_is_' + ct.identifier] = True
        if self.router:
            response.data['parent'] = self.router.serialize(parent)
        return parent
