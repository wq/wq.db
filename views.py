from djangorestframework import views, status, response, mixins
from wq.db.renderers import JSONRenderer, XMLRenderer, HTMLRenderer, AMDRenderer

from django.contrib.contenttypes.models import ContentType
from wq.db.identify.models import Identifier, IdentifiedModel
from wq.db.annotate.models import Annotation, AnnotatedModel, AnnotationType
from wq.db import resources

from django.conf import settings
from wq.db.util import get_config, has_perm, geturlbase, user_dict
from wq.db.util import get_ct, get_id, get_object_id

from django.contrib.auth import authenticate, login, logout

_FORBIDDEN_RESPONSE = "Sorry %s, you do not have permission to %s this %s."
_RENDERERS = [HTMLRenderer, JSONRenderer, XMLRenderer, AMDRenderer]

class View(views.View):
    renderers = _RENDERERS
    
    @property
    def template(self):
        if getattr(self, 'resource', None) is None:
            template = type(self).__name__.replace('View', '').lower()
        else:
            model = getattr(self, 'model', self.resource.model)
            ctid   = get_id(get_ct(model))
            if self._suffix == 'List':
                template = ctid + '_list'
            else:
                template = ctid + '_detail'
        return template

class InstanceModelView(View, views.InstanceModelView):
    def get_instance(self, *args, **kwargs):
        if issubclass(self.resource.model, IdentifiedModel):
            return self.resource.model.objects.get_by_identifier(kwargs['pk'])
        else:
            return super(InstanceModelView, self).get_instance(*args, **kwargs)

    def put(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not has_perm(request.user, ct, 'change'):
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
        if not has_perm(request.user, ct, 'delete'):
            forbid(request.user, ct, 'delete')
        return super(InstanceModelView, delete).put(request, *args, **kwargs)

class ListOrCreateModelView(View, mixins.PaginatorMixin, 
                            views.ListOrCreateModelView):
    annotations = {}
    def get_query_kwargs(self, *args, **kwargs):
        for key, val in self.request.GET.items():
            if key in ('_', 'page'):
                continue
            kwargs[key] = val if isinstance(val, unicode) else val[0]
            for f in self.resource.model._meta.fields:
                if f.name == key and hasattr(f, 'rel'):
                    if issubclass(f.rel.to, IdentifiedModel):
                        kwargs[key] = f.rel.to.objects.get_by_identifier(val)
        kwargs = super(ListOrCreateModelView, self).get_query_kwargs(*args, **kwargs)
        return kwargs

    @property
    def CONTENT(self):
        content = super(ListOrCreateModelView, self).CONTENT
        if issubclass(self.resource.model, AnnotatedModel):
            ct = ContentType.objects.get_for_model(self.resource.model)
            atypes = AnnotationType.objects.filter(contenttype=ct)
            for at in atypes:
                fname = 'annotation-%s' % at.pk
                if fname in content:
                    self.annotations[at] = content[fname]
                    del content[fname]
                else:
                    self.annotations[at] = ""
        return content

    def get(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not has_perm(request.user, ct, 'view'):
            forbid(request.user, ct, 'view')
        return super(ListOrCreateModelView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        ct = ContentType.objects.get_for_model(self.resource.model)
        if not has_perm(request.user, ct, 'add'):
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
        result['list'] = result['results']
        del result['results']
        return result

class ConfigView(View):
    def get(self, request, *args, **kwargs):
        return get_config(request.user)

class LoginView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return {
                'user':   user_dict(request.user),
                'config': get_config(request.user)
            }
        else:
            return {}

    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return {
                'user':   user_dict(user),
                'config': get_config(user)
            }
        else:
            return {}

class LogoutView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            logout(request)
            return True
        else:
            return {}

class DisambiguateView(View):
    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']
        result = {
            'slug': slug
        }
        ids = Identifier.objects.filter_by_identifier(slug)
        if len(ids) == 0:
            result['message'] = "Page Not Found"
            raise response.ErrorResponse(status.HTTP_404_NOT_FOUND, result)

        result['list'] = [
            {
                'url':   '%s/%s' % (geturlbase(ident.content_type),
                                    get_object_id(ident.content_object)),
                'type':  unicode(ident.content_type),
                'label': unicode(ident.content_object)
            }
            for ident in ids
        ]
        if len(ids) == 1:
            result['message'] = "Found"
            result = response.Response(status.HTTP_302_FOUND, result,
                {'Location': '/' + result['list'][0]['url']}
            )
        else:
            result['message'] = "Multiple Matches Found"

        return result


def forbid(user, ct, perm):
    raise response.ErrorResponse(status.HTTP_403_FORBIDDEN, {
        'details': _FORBIDDEN_RESPONSE % (user, perm, ct)
    })
