from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

from django.conf import settings
from rest_framework.settings import api_settings
from rest_framework.response import Response

from .models import ContentType, get_ct
from .permissions import has_perm
from .views import View, InstanceModelView, ListOrCreateModelView

class Router(object):
    _serializers = {}
    _views = {}
    _extra_pages = {}

    def register_serializer(self, model, serializer):
        self._serializers[model] = serializer
    
    def register_views(self, model, listview=None, instanceview=None):
        self._views[model] = listview, instanceview

    def get_serializer_for_model(self, model_class):

        if model_class in self._serializers:
            serializer = self._serializers[model_class]
        else:
            # Make sure we're not dealing with a proxy
            model_class = get_ct(model_class).model_class()
            if model_class in self._serializers:
                serializer = self._serializers[model_class]
            else:
                serializer = api_settings.DEFAULT_MODEL_SERIALIZER_CLASS

        class Serializer(serializer):
            class Meta(serializer.Meta):
                model = model_class
        return Serializer

    def serialize(self, obj):
        serializer = self.get_serializer_for_model(obj)
        return serializer().to_native(obj)

    def get_views_for_model(self, model):
        if model in self._views:
            listview, detailview = self._views[model]
        else:
            # Make sure we're not dealing with a proxy
            model = get_ct(model).model_class()
            if model in self._views:
                listview, detailview = self._views[model]
            else:
                listview, detailview = None, None
        listview = listview or ListOrCreateModelView
        detailview = detailview or InstanceModelView
        serializer = self.get_serializer_for_model(model)

        # pass router to view so that serializer can load appropriate model serializers
        listview = listview.as_view(
            model = model,
            router = self
        )
        detailview = detailview.as_view(
            model = model,
            router = self
        )
        return listview, detailview

    def get_config(self, user):
         pages = {}
         for page in self._extra_pages:
             pages[page] = self._extra_pages[page]
         for ct in ContentType.objects.all():
             if not has_perm(user, ct, 'view'):
                 continue
             cls = ct.model_class()
             if cls is None:
                 continue
             info = {'name': ct.name, 'url': ct.urlbase, 'list': True, 'parents': [], 'children': []}
             for perm in ('add', 'change', 'delete'):
                 if has_perm(user, ct, perm):
                     info['can_' + perm] = True

             for pct in ct.get_parents():
                 if has_perm(user, pct, 'view'):
                     info['parents'].append(pct.identifier)

             for cct in ct.get_children():
                 if has_perm(user, cct, 'view'):
                     info['children'].append(cct.identifier)

             for name in ('annotated', 'identified', 'located', 'related'):
                 info[name] = getattr(ct, 'is_' + name)

             pages[ct.identifier] = info
         return {'pages': pages}

    def add_page_config(self, name, config):
        self._extra_pages[name] = config

    def get_config_view(self):
        class ConfigView(View):
            def get(this, request, *args, **kwargs):
                return Response(self.get_config(request.user))
        return ConfigView.as_view()

    @property 
    def urls(self):
        from django.conf.urls import patterns, include, url
        configview = self.get_config_view()
        urlpatterns = patterns('', 
            url('^config/?$',                configview),
            url('^config\.(?P<format>\w+)$', configview)
        )

        for ct in ContentType.objects.all():
                
            cls = ct.model_class()
            if cls is None:
                continue

            listview, detailview = self.get_views_for_model(cls)
            urlbase = ct.urlbase

            urlpatterns += patterns('',
                url('^' + urlbase + r'/?$',  listview),
                url('^' + urlbase + r'\.(?P<format>\w+)$', listview),
                url('^' + urlbase + r'/new$', listview),
                url('^' + urlbase + r'/(?P<slug>[^\/\?]+)\.(?P<format>\w+)$', detailview),
                url('^' + urlbase + r'/(?P<slug>[^\/\?]+)/edit$', detailview),
                url('^' + urlbase + r'/(?P<slug>[^\/\?]+)/?$', detailview)
            )

            for pct in ct.get_all_parents():
                if pct.model_class() is None:
                    continue
                purl = '^' + pct.urlbase + r'/(?P<' + pct.identifier + '>[^\/\?]+)/' + urlbase
                urlpatterns += patterns('',
                    url(purl + '/?$', listview),
                    url(purl + '\.(?P<format>\w+)$', listview),
                )

            for cct in ct.get_all_children():
                cbase = cct.urlbase
                curl = '^%s-by-%s'% (cbase, ct.identifier)
                kwargs = {'target': cbase}
                urlpatterns += patterns('',
                    url(curl + '/?$', listview, kwargs),
                    url(curl + '\.(?P<format>\w+)$', listview, kwargs),
                )
        return urlpatterns

router = Router()

def autodiscover():
    for app_name in settings.INSTALLED_APPS:
        app = import_module(app_name)
        if module_has_submodule(app, 'serializers'):
            import_module(app_name + '.serializers')
        if module_has_submodule(app, 'views'):
            import_module(app_name + '.views')
