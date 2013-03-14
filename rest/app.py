from django.contrib.contenttypes.models import ContentType

from wq.db.rest import views, util, serializers

from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

class Router(object):
    _serializers = {}
    _views = {}
    _extra_pages = {}

    def register_serializer(model, serializer):
        self._serializers[model] = serializer
    
    def register_views(model, listview=None, instanceview=None):
        self._views[model] = listview, instanceview

    def get_serializer_for_model(self, model):
        return api_settings.

    def get_view_for_model(self, model):
        if model_class in _view_map:
            listview, detailview = self._views[model_class]
        else:
            listview, detailview = None, None
        listview = listview or ListOrCreateModelView
        detailview = detailview or InstanceModelView

        # pass router to view so that serializer can load appropriate model serializers
        res = resources.get_for_model(model_class)
        return listview.as_view(resource=res), detailview.as_view(resource=res)

    def get_serializer_for_model(self, model, depth=0):
        return self._serializers.get(model, self.create_serializer(model))

    def create_serializer(self, model, depth=0):
        class ModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = model
                depth = depth
        return ModelSerializer

    def get_config(self, user):
         from django.conf import settings
         if hasattr(settings, 'REST_CONFIG'):
             return settings.REST_CONFIG
         pages = {}
         for page in _extra_pages:
             pages[page] = _extra_pages[page]
         for ct in ContentType.objects.all():
             if not has_perm(user, ct, 'view'):
                 continue
             cls = ct.model_class()
             if cls is None:
                 continue
             info = {'name': ct.name, 'url': geturlbase(ct), 'list': True, 'parents': [], 'children': []}
             for perm in ('add', 'change', 'delete'):
                 if has_perm(user, ct, perm):
                     info['can_' + perm] = True

             for pct in get_parents(ct):
                 if has_perm(user, pct, 'view'):
                     info['parents'].append(get_id(pct))

             for cct in get_children(ct):
                 if has_perm(user, cct, 'view'):
                     info['children'].append(get_id(cct))

             info['annotated'] = issubclass(cls, AnnotatedModel)
             info['identified'] = issubclass(cls, IdentifiedModel)
             pages[get_id(ct)] = info
         return {'pages': pages}

    def add_page_config(name, config):
       self._extra_pages[name] = config

    def get_config_view(self):
        class ConfigView(View):
            def get(this, request, *args, **kwargs):
                return self.get_config(request.user)
        return ConfigView.as_view()

    @property 
    def urls(self):
        from django.conf.urls.defaults import patterns, include, url
        configview = self.get_config_view()
        urlpatterns = patterns('', 
            url('^config/?$',                configview),
            url('^config\.(?P<format>\w+)$', configview)
        )

        for ct in ContentType.objects.all():
                
            cls = ct.model_class()
            if cls is None:
                continue

            listview, detailview = views.get_for_model(cls)
            urlbase = util.geturlbase(ct)

            urlpatterns += patterns('',
                url('^' + urlbase + r'/?$',  listview),
                url('^' + urlbase + r'\.(?P<format>\w+)$', listview),
                url('^' + urlbase + r'/new$', listview),
                url('^' + urlbase + r'/(?P<pk>[^\/\?]+)\.(?P<format>\w+)$', detailview),
                url('^' + urlbase + r'/(?P<pk>[^\/\?]+)/edit$', detailview),
                url('^' + urlbase + r'/(?P<pk>[^\/\?]+)/?$', detailview)
            )

            for pct in util.get_all_parents(ct):
                purl = '^' + util.geturlbase(pct) + r'/(?P<' + util.get_id(pct) + '>[^\/\?]+)/' + urlbase
                urlpatterns += patterns('',
                    url(purl + '/?$', listview),
                    url(purl + '\.(?P<format>\w+)$', listview),
                )

            for cct in util.get_all_children(ct):
                cbase = util.geturlbase(cct)
                curl = '^%s-by-%s'% (cbase, util.get_id(ct))
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
