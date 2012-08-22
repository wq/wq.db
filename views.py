from djangorestframework import views, status, response
from djangorestframework.renderers import BaseRenderer, JSONRenderer, XMLRenderer

from django.contrib.contenttypes.models import ContentType
from wq.db.annotate.models import Annotation, AnnotatedModel, AnnotationType
from wq.db import resources

_FORBIDDEN_RESPONSE = "Sorry %s, you do not have permission to %s this %s."
_FORBIDDEN_APPS = ('auth','sessions','admin','contenttypes','reversion','south')

class RedirectRenderer(BaseRenderer):
    media_type = 'text/html'
    def render(self, obj=None, accept=None):
        path = self.view.request.path
        self.view.response.status = status.HTTP_302_FOUND
        self.view.response.headers['Location'] = '/#' + path
        return 'Redirecting...'

class View(views.View):
    renderers = [RedirectRenderer, JSONRenderer, XMLRenderer]

class InstanceModelView(views.InstanceModelView):
    renderers = [RedirectRenderer, JSONRenderer, XMLRenderer]
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

class ListOrCreateModelView(views.ListOrCreateModelView):
    renderers = [RedirectRenderer, JSONRenderer, XMLRenderer]
    annotations = {}
    def get_query_kwargs(self, *args, **kwargs):
        for key, val in self.request.GET.items():
            kwargs[key] = val if isinstance(val, unicode) else val[0]
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

class Config(View):
    def get(request, *args, **kwargs):
       pages = {}
       for ct in ContentType.objects.all():
           if not has_perm(request.user, ct, 'view'):
               continue
           cls = ct.model_class()
           if cls is None:
               continue
           info = {'name': ct.name, 'url': geturlbase(ct), 'list': True, 'parents': [], 'children': []}
           for perm in ('add', 'change', 'delete'):
               if has_perm(request.user, ct, perm):
                   info['can_' + perm] = True
           for f in cls._meta.fields:
               if f.rel is not None and type(f.rel).__name__ == 'ManyToOneRel':
                   pct = ContentType.objects.get_for_model(f.rel.to)
                   info['parents'].append(resources.get_id(pct))

           for r in cls._meta.get_all_related_objects():
               cct = ContentType.objects.get_for_model(r.model)
               info['children'].append(resources.get_id(cct))

           info['annotated'] = issubclass(cls, AnnotatedModel)
           pages[resources.get_id(ct)] = info
       return {'pages': pages}

def geturlbase(ct):
    cls = ct.model_class()
    return getattr(cls, 'slug', resources.get_id(ct) + 's')


def has_perm(user, ct, perm):
    if ct.app_label in _FORBIDDEN_APPS and not user.is_superuser:
        return False
    elif perm == 'view':
        return True

    perm = '%s.%s_%s' % (ct.app_label, ct.model, perm)
    if user.is_authenticated():
        return user.has_perm(perm)
    else:
        from django.conf import settings
        return perm in getattr(settings, 'ANONYMOUS_PERMISSIONS', {})

def forbid(user, ct, perm):
    raise response.ErrorResponse(status.HTTP_403_FORBIDDEN, {
        'details': _FORBIDDEN_RESPONSE % (user, perm, ct)
    })
