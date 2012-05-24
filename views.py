from djangorestframework.views import (View as RestView, 
     InstanceModelView as RestInstanceModelView,
     ListOrCreateModelView as RestListOrCreateModelView)
from djangorestframework.renderers import BaseRenderer, JSONRenderer

from django.contrib.contenttypes.models import ContentType
from wq.db.annotate.models import Annotation, AnnotatedModel, AnnotationType
from wq.db import resources

class RedirectRenderer(BaseRenderer):
    def render(self, obj=None, accept=None):
        path = self.view.request.path
        self.view.response.status = 302
        self.view.response.headers['Location'] = '/#' + path
        return 'Redirecting...'

class View(RestView):
    renderers = [RedirectRenderer, JSONRenderer]

class InstanceModelView(RestInstanceModelView):
    renderers = [RedirectRenderer, JSONRenderer]
    def put(self, request, *args, **kwargs):
        res = super(InstanceModelView, self).put(request, *args, **kwargs)

        if issubclass(self.resource.model, AnnotatedModel):
            ct = ContentType.objects.get_for_model(self.resource.model)
            atypes = AnnotationType.objects.filter(contenttype=ct)
            for at in atypes:
                fname = 'annotation-%s' % at.pk
                if fname in self.CONTENT:
                    annot, isnew = Annotation.objects.get_or_create(
                        type=at, content_type=ct, object_id=res.pk)
                    annot.value = self.CONTENT[fname]
                    annot.save()
        return res

class ListOrCreateModelView(RestListOrCreateModelView):
    renderers = [RedirectRenderer, JSONRenderer]
    annotations = {}
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

    def post(self, request, *args, **kwargs):
        res = super(ListOrCreateModelView, self).post(request, *args, **kwargs)

        if issubclass(self.resource.model, AnnotatedModel):
            ct = ContentType.objects.get_for_model(self.resource.model)
            for at, val in self.annotations.iteritems():
                annot, isnew = Annotation.objects.get_or_create(
                type=at, content_type=ct, object_id=res.raw_content.id)
                annot.value = val
                annot.save()
        return res

class Config(View):
    def get(req, fmt):
       pages = {}
       for ct in ContentType.objects.all():
           cls = ct.model_class()
           if cls is None:
               continue
           info = {'name': ct.name, 'url': geturlbase(ct), 'list': True, 'parents': [], 'children': []}
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
