from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule
from django.conf.urls import patterns, include, url
from django.core.paginator import Paginator

from django.conf import settings
from rest_framework.settings import api_settings
from rest_framework.response import Response

from .models import ContentType, get_ct
from .permissions import has_perm
from .views import View, SimpleView, InstanceModelView, ListOrCreateModelView


class Router(object):
    _serializers = {}
    _querysets = {}
    _views = {}
    _extra_pages = {}
    _custom_config = {}

    FORMAT = r'\.(?P<format>\w+)$'
    SLUG = r'(?P<slug>[^\/\?]+)'

    def register_serializer(self, model, serializer):
        self._serializers[model] = serializer

    def register_queryset(self, model, queryset):
        self._querysets[model] = queryset

    def register_views(self, model, listview=None, instanceview=None):
        self._views[model] = listview, instanceview

    def get_serializer_for_model(self, model_class, serializer_depth=None):

        if model_class in self._serializers:
            serializer = self._serializers[model_class]
        else:
            # Make sure we're not dealing with a proxy
            real_model = get_ct(model_class, True).model_class()
            if real_model in self._serializers:
                serializer = self._serializers[real_model]
            else:
                serializer = api_settings.DEFAULT_MODEL_SERIALIZER_CLASS

        class Serializer(serializer):
            class Meta(serializer.Meta):
                depth = serializer_depth
                model = model_class
        return Serializer

    def serialize(self, obj, many=False, depth=None):
        if many:
            # assume obj is a queryset
            model = obj.model
            if depth is None:
                depth = 0
        else:
            model = obj
            if depth is None:
                depth = 1
        serializer = self.get_serializer_for_model(model, depth)
        return serializer(obj, many=many, context={'router': self}).data

    def get_paginate_by_for_model(self, model_class):
        name = get_ct(model_class).identifier
        if name in self._custom_config:
            paginate_by = self._custom_config[name].get('per_page', None)
            if paginate_by:
                return paginate_by
        return api_settings.PAGINATE_BY

    def paginate(self, model, page_num, request=None):
        obj_serializer = self.get_serializer_for_model(model)
        paginate_by = self.get_paginate_by_for_model(model)
        paginator = Paginator(self.get_queryset_for_model(model), paginate_by)
        page = paginator.page(page_num)

        class Serializer(api_settings.DEFAULT_PAGINATION_SERIALIZER_CLASS):
            class Meta:
                object_serializer_class = obj_serializer
        return Serializer(
            instance=page,
            context={'router': self, 'request': request}
        ).data

    def get_queryset_for_model(self, model):
        if model in self._querysets:
            return self._querysets[model]
        return model.objects.all()

    def get_views_for_model(self, model):
        if model in self._views:
            listview, detailview = self._views[model]
        else:
            # Make sure we're not dealing with a proxy
            real_model = get_ct(model, True).model_class()
            if real_model in self._views:
                listview, detailview = self._views[real_model]
            else:
                listview, detailview = None, None
        listview = listview or ListOrCreateModelView
        detailview = detailview or InstanceModelView
        serializer = self.get_serializer_for_model(model)

        # pass router to view for use by get_serializer_class
        listview = listview.as_view(
            model=model,
            router=self
        )
        detailview = detailview.as_view(
            model=model,
            router=self
        )
        return listview, detailview

    def get_config(self, user):
        pages = {}
        for page in self._extra_pages:
            conf, view = self.get_page(page)
            pages[page] = conf
        for ct in ContentType.objects.all():
            if not has_perm(user, ct, 'view'):
                continue
            cls = ct.model_class()
            if cls is None:
                continue
            info = {
                'name': ct.name,
                'url': ct.urlbase,
                'list': True,
                'parents': [],
                'children': []
            }
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
                if getattr(ct, 'is_' + name):
                    info[name] = True

            if ct.is_located or ct.has_geo_fields:
                info['map'] = True

            for field in cls._meta.fields:
                if field.choices:
                    info.setdefault('choices', {})
                    info['choices'][field.name] = [{
                        'value': val,
                        'label': unicode(label)
                    } for val, label in field.choices]

            for name in ('annotationtype', 'annotation'):
                if ct.identifier != name and getattr(ct, 'is_' + name):
                    pages[name] = {'alias': ct.identifier}

            if ct.identifier in self._custom_config:
                info.update(self._custom_config[ct.identifier])
            pages[ct.identifier] = info

        return {'pages': pages}

    def add_page(self, name, config, view=None):
        self._extra_pages[name] = config, view

    def customize_page(self, name, config):
        self._custom_config[name] = config

    def get_page(self, page):
        config, view = self._extra_pages[page]
        if view is None:
            class PageView(SimpleView):
                template_name = page + '.html'
            view = PageView
        return config, view.as_view()

    def get_config_view(self):
        class ConfigView(View):
            def get(this, request, *args, **kwargs):
                return Response(self.get_config(request.user))
        return ConfigView.as_view()

    def get_multi_view(self):
        class MultipleListView(View):
            def get(this, request, *args, **kwargs):
                conf_by_url = {
                    conf['url']: (page, conf)
                    for page, conf
                    in self.get_config(request.user)['pages'].items()
                }
                urls = request.GET.get('lists', '').split(',')
                result = {}
                for url in urls:
                    if url not in conf_by_url:
                        continue
                    page, conf = conf_by_url[url]
                    ct = ContentType.objects.get(model=page)
                    cls = ct.model_class()
                    result[url] = self.paginate(cls, 1, request)
                return Response(result)
        return MultipleListView.as_view()

    def make_patterns(self, urlbase, listview, detailview=None):
        fmt = self.FORMAT
        slug = self.SLUG
        if urlbase == '':
            detailurl = '^'
            listurl = '^'
        else:
            detailurl = '^' + urlbase + '/'
            listurl = '^' + urlbase
        result = patterns('',
            url(listurl + r'/?$', listview),
            url(listurl + fmt, listview),
        )
        if detailview is None:
            return result

        result += patterns('',
            url(detailurl + r'(?P<mode>new)$', detailview),
            url(detailurl + r'(?P<mode>new)' + fmt, detailview),
            url(detailurl + slug + fmt, detailview),
            url(detailurl + slug + r'/(?P<mode>edit)$', detailview),
            url(detailurl + slug + r'/(?P<mode>edit)' + fmt, detailview),
            url(detailurl + slug + '/?$', detailview)
        )
        return result

    @property
    def urls(self):
        root_views = None, None

        # /config.js
        urlpatterns = self.make_patterns('config', self.get_config_view())

        # /multi.json
        urlpatterns += self.make_patterns('multi', self.get_multi_view())

        # Custom pages
        for page in self._extra_pages:
            conf, view = self.get_page(page)
            if conf['url'] == '':
                root_views = view, None
                continue
            urlpatterns += self.make_patterns(conf['url'], view)

        # Model list & detail views
        for ct in ContentType.objects.all():

            cls = ct.model_class()
            if cls is None:
                continue

            listview, detailview = self.get_views_for_model(cls)
            if ct.urlbase == '':
                root_views = listview, detailview
                continue

            urlpatterns += self.make_patterns(ct.urlbase, listview, detailview)

            for pct in ct.get_all_parents():
                if pct.model_class() is None:
                    continue
                if pct.urlbase == '':
                    purlbase = ''
                else:
                    purlbase = pct.urlbase + '/'
                purl = (
                    '^' + purlbase + r'(?P<' + pct.identifier
                    + '>[^\/\?]+)/' + ct.urlbase
                )
                urlpatterns += patterns('',
                    url(purl + '/?$', listview),
                    url(purl + self.FORMAT, listview),
                )

            for cct in ct.get_all_children():
                cbase = cct.urlbase
                curl = '^%s-by-%s' % (cbase, ct.identifier)
                kwargs = {'target': cbase}
                urlpatterns += patterns('',
                    url(curl + '/?$', listview, kwargs),
                    url(curl + self.FORMAT, listview, kwargs),
                )

        # View for root url - could be either a custom page or list/detail
        # views for a model. In the latter case /[slug] will catch any
        # unmatched url and point it to the detail view, which is why this
        # rule is last.
        if root_views[0] is not None:
            listview, detailview = root_views
            urlpatterns += self.make_patterns('', listview, detailview)

        return urlpatterns

    @property
    def version(self):
        if not hasattr(self, '_version'):
            vtxt = getattr(settings, 'VERSION_TXT', None)
            if vtxt is None:
                self._version = None
            else:
                vfile = open(vtxt, 'r')
                self._version = vfile.read()
                vfile.close()
        return self._version

router = Router()


def autodiscover():
    for app_name in settings.INSTALLED_APPS:
        app = import_module(app_name)
        if module_has_submodule(app, 'serializers'):
            import_module(app_name + '.serializers')
        if module_has_submodule(app, 'views'):
            import_module(app_name + '.views')
