from rest_framework.generics import GenericAPIView as RestGenericAPIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework import status, viewsets
from .model_tools import get_ct, get_object_id, get_by_identifier
from django.db.models.fields import FieldDoesNotExist


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
        elif self.action and self.action != 'metadata':
            suffix = self.action
        else:
            suffix = 'list'
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
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        serializer.add_lookups(response.data)
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
        for key in list(init.keys()):
            try:
                field = self.model._meta.get_field(key)
            except FieldDoesNotExist:
                del init[key]
            else:
                if field.rel:
                    fk_model = field.rel.to
                    try:
                        obj = get_by_identifier(fk_model.objects, init[key])
                    except fk_model.DoesNotExist:
                        del init[key]
                    else:
                        init[key] = obj.pk

        obj = self.model(**init)
        serializer = self.get_serializer(obj)
        data = serializer.data
        serializer.add_lookups(data)
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

    def list(self, request, *args, **kwargs):
        response = super(ModelViewSet, self).list(
            request, *args, **kwargs
        )
        if not isinstance(response.data, dict):
            return response

        if self.target:
            response.data['target'] = self.target
        ct = get_ct(self.model)
        for pct, fields in ct.get_foreign_keys().items():
            if len(fields) == 1:
                self.get_parent(pct, fields[0], response)
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

    def update(self, request, *args, **kwargs):
        response = super(ModelViewSet, self).update(
            request, *args, **kwargs
        )
        if not request.accepted_media_type.startswith('text/html'):
            # JSON request, assume client will handle redirect
            return response

        # HTML request, probably a form post from an older browser
        if response.status_code == status.HTTP_200_OK:
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
        if page != ct.identifier and self.router:
            # Optional: return to detail view of a parent model
            pconf = self.router.get_page_config(page)
            if pconf.get('list', None) and mode != "list":
                oid = response.data.get(page + '_id', None)
        else:
            # Default: return to detail view of the saved model
            pconf = conf
            if mode != "list":
                oid = response.data['id']

        url = "/" + pconf['url']
        if pconf['url'] and pconf.get('list', None):
            url += "/"
        if oid:
            url += str(oid)
            if mode == "edit":
                url += "/edit"

        return Response(
            {'detail': 'Created'},
            status=status.HTTP_302_FOUND,
            headers={'Location': url}
        )

    def saveerror(self, request, response):
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

    def get_parent(self, ct, kwarg_name, response):
        pid = self.kwargs.get(kwarg_name, None)
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
        response.data['parent_page'] = ct.identifier
        response.data['page_config'] = get_ct(self.model).get_config()
        if self.router:
            response.data['parent'] = self.router.serialize(parent)
        return parent

    def head(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
