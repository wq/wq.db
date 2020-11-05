from django.utils.encoding import force_text
from django.conf.urls import url
from django.db.utils import DatabaseError

from django.conf import settings
from rest_framework.routers import DefaultRouter, Route
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.settings import api_settings
from rest_framework.response import Response

from .model_tools import get_ct
from .permissions import has_perm
from .views import SimpleViewSet, ModelViewSet
from .serializers import ModelSerializer
from .exceptions import ImproperlyConfigured

import inspect


class ModelRouter(DefaultRouter):
    _models = set()
    _serializers = {}
    _fields = {}
    _querysets = {}
    _filters = {}
    _cache_filters = {}
    _viewsets = {}
    _extra_pages = {}
    _config = {}
    _page_names = {}
    _page_models = {}
    _url_models = {}
    _extra_config = {}

    include_root_view = False
    include_config_view = True
    include_multi_view = True

    default_serializer_class = ModelSerializer

    def __init__(self, trailing_slash=False):
        """
        Initialize all routes.

        Args:
            self: (todo): write your description
            trailing_slash: (todo): write your description
        """
        # Add trailing slash for HTML list views
        self.routes.append(Route(
            url=r'^{prefix}/$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ))
        super(ModelRouter, self).__init__(trailing_slash=trailing_slash)

    def register_model(self, model, viewset=None, serializer=None, fields=None,
                       queryset=None, filter=None, cache_filter=None,
                       **kwargs):
        """
        Register a model.

        Args:
            self: (todo): write your description
            model: (str): write your description
            viewset: (todo): write your description
            serializer: (str): write your description
            fields: (todo): write your description
            queryset: (todo): write your description
            filter: (todo): write your description
            cache_filter: (todo): write your description
        """
        if isinstance(model, str) and '.' in model:
            from django.db.models import get_model
            model = get_model(*model.split('.'))

        if viewset:
            self.register_viewset(model, viewset)
        if queryset is not None:
            self.register_queryset(model, queryset)
        if filter:
            self.register_filter(model, filter)
        if cache_filter:
            self.register_cache_filter(model, cache_filter)
            kwargs['cache'] = 'filter'

        if 'name' not in kwargs:
            kwargs['name'] = model._meta.model_name
        if 'url' not in kwargs:
            url = force_text(model._meta.verbose_name_plural)
            kwargs['url'] = url.replace(' ', '')

        other_model = self._page_models.get(kwargs['name'], None)
        if other_model:
            raise ImproperlyConfigured(
                "Could not register %s: "
                "the name '%s' was already registered for %s"
                % (model, kwargs['name'], other_model)
            )

        other_model = self._url_models.get(kwargs['url'], None)
        if other_model:
            raise ImproperlyConfigured(
                "Could not register %s: "
                "the url '%s' was already registered for %s"
                % (model, kwargs['url'], other_model)
            )

        self.register_config(model, kwargs)

        if serializer:
            self.register_serializer(model, serializer)

        if fields:
            self.register_fields(model, fields)

        self._models.add(model)
        self._page_names[model] = kwargs['name']
        self._page_models[kwargs['name']] = model
        self._url_models[kwargs['url']] = model

    def register_viewset(self, model, viewset):
        """
        Register a modelsetsetsetsetsetsetset with_view.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            viewset: (todo): write your description
        """
        self._viewsets[model] = viewset

    def register_serializer(self, model, serializer):
        """
        Register a serializer.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            serializer: (todo): write your description
        """
        self._serializers[model] = serializer
        self._base_config = None

    def register_fields(self, model, fields):
        """
        Register the given model.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            fields: (todo): write your description
        """
        self._fields[model] = fields

    def register_queryset(self, model, queryset):
        """
        Registers a queryset.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            queryset: (str): write your description
        """
        self._querysets[model] = queryset

    def register_filter(self, model, filter):
        """
        Register a filter.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            filter: (dict): write your description
        """
        self._filters[model] = filter

    def register_cache_filter(self, model, cache_filter):
        """
        Register a filter filter.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            cache_filter: (todo): write your description
        """
        self._cache_filters[model] = cache_filter

    def register_config(self, model, config):
        """
        Registers a configuration.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            config: (todo): write your description
        """
        for key in ('partial', 'reversed', 'max_local_pages'):
            if key in config:
                raise ImproperlyConfigured(
                    '"%s" is deprecated in favor of "cache"' % key
                )
        self._config[model] = config
        self._base_config = None

    def update_config(self, model, **kwargs):
        """
        Updates the configuration of a model.

        Args:
            self: (todo): write your description
            model: (str): write your description
        """
        if model not in self._config:
            raise RuntimeError("%s must be registered first" % model)
        for key in ('partial', 'reversed', 'max_local_pages'):
            if key in kwargs:
                raise ImproperlyConfigured(
                    '"%s" is deprecated in favor of "cache"' % key
                )
        self._config[model].update(kwargs)
        self._base_config = None

    def set_extra_config(self, **extra):
        """
        Sets the extra configuration.

        Args:
            self: (todo): write your description
            extra: (dict): write your description
        """
        self._extra_config.update(extra)
        self._base_config = None

    def get_default_serializer_class(self, model_class):
        """
        Return the default class for the given model_class.

        Args:
            self: (todo): write your description
            model_class: (todo): write your description
        """
        return self.default_serializer_class

    def get_class(self, classes, model_class, default=lambda model: None):
        """
        Return the class for classes.

        Args:
            self: (todo): write your description
            classes: (int): write your description
            model_class: (str): write your description
            default: (todo): write your description
            model: (str): write your description
        """
        if model_class in classes:
            return classes[model_class]
        else:
            # Make sure we're not dealing with a proxy
            real_model = model_class._meta.concrete_model
            if real_model in classes:
                return classes[real_model]
            else:
                if real_model not in self._config:
                    # FIXME: Probably can just use default instead of erroring
                    raise ImproperlyConfigured(
                        "%s is not registered!" % real_model
                    )
                return default(real_model)

    def get_serializer_for_model(self, model_class, serializer_depth=None):
        """
        Get a serializer for a given model.

        Args:
            self: (todo): write your description
            model_class: (todo): write your description
            serializer_depth: (todo): write your description
        """
        serializer = self.get_class(
            self._serializers, model_class,
            self.get_default_serializer_class
        )

        meta = getattr(serializer, 'Meta', object)
        if not getattr(meta, 'model', None):
            if getattr(meta, 'fields', None) or getattr(meta, 'exclude', None):
                include_fields = None
            else:
                include_fields = self._fields.get(model_class, None)
                if not include_fields:
                    raise ImproperlyConfigured(
                        "No serializer fields defined for %s" % model_class
                    )
            serializer = serializer.for_model(
                model_class, include_fields=include_fields
            )

        if serializer_depth is not None:
            if serializer_depth != getattr(meta, 'depth', None):
                serializer = serializer.for_depth(serializer_depth)

        meta = getattr(serializer, 'Meta', object)
        conf = self._config.get(model_class, None)
        if not conf:
            conf = self._config.get(model_class._meta.concrete_model, None)

        if conf:
            wq_conf = getattr(meta, 'wq_config', {}).copy()
            wq_conf.update(conf)
            meta.wq_config = wq_conf
            serializer.Meta = meta

        return serializer

    def serialize(self, obj, many=False, depth=None, request=None):
        """
        Serialize an object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            many: (bool): write your description
            depth: (todo): write your description
            request: (todo): write your description
        """
        if many:
            # assume obj is a queryset
            model = obj.model
            if depth is None:
                depth = 0
        else:
            model = obj.__class__
            if depth is None:
                depth = 1
        serializer = self.get_serializer_for_model(model, depth)
        context = {'router': self}
        if request:
            context['request'] = request
        return serializer(obj, many=many, context=context).data

    def get_paginate_by_for_model(self, model_class):
        """
        Return a paginate model by model.

        Args:
            self: (todo): write your description
            model_class: (todo): write your description
        """
        config = self.get_model_config(model_class) or {}
        paginate_by = config.get('per_page', None)
        if paginate_by:
            return paginate_by
        return api_settings.PAGE_SIZE

    def paginate(self, model, page_num, request):
        """
        Paginate the model.

        Args:
            self: (todo): write your description
            model: (todo): write your description
            page_num: (int): write your description
            request: (todo): write your description
        """
        # FIXME: should copy() before modifying but doing so causes recursion
        request.GET = {
            'page': page_num,
        }
        view = self.get_viewset_for_model(model).as_view(
            actions={'get': 'list'},
        )
        return view(request._request).data

    def get_queryset_for_model(self, model, request=None):
        """
        Return queryset of all pages.

        Args:
            self: (todo): write your description
            model: (str): write your description
            request: (todo): write your description
        """
        if model in self._page_models:
            model = self._page_models[model]
        if model in self._querysets:
            qs = self._querysets[model]
        else:
            qs = model.objects.all()
        if request and model in self._filters:
            qs = self._filters[model](qs, request)
        return qs

    def get_cache_filter_for_model(self, model):
        """
        Returns a queryset for the given model.

        Args:
            self: (todo): write your description
            model: (str): write your description
        """
        return self._cache_filters.get(model, lambda qs, req: qs)

    def get_lookup_for_model(self, model_class):
        """
        Return the lookup for a model.

        Args:
            self: (todo): write your description
            model_class: (todo): write your description
        """
        config = self.get_model_config(model_class) or {}
        return config.get('lookup', 'pk')

    def get_viewset_for_model(self, model_class):
        """
        Get a modelsetset for the given model_class.

        Args:
            self: (todo): write your description
            model_class: (todo): write your description
        """
        if model_class in self._page_models:
            model_class = self._page_models[model_class]
        viewset = self.get_class(
            self._viewsets, model_class, lambda d: ModelViewSet
        )
        lookup = self.get_lookup_for_model(model_class)

        per_page = self.get_paginate_by_for_model(model_class)
        if per_page != api_settings.PAGE_SIZE:
            class CustomPagination(api_settings.DEFAULT_PAGINATION_CLASS):
                page_size = per_page
        else:
            CustomPagination = None

        class ViewSet(viewset):
            model = model_class
            router = self
            lookup_field = lookup

            if CustomPagination:
                pagination_class = CustomPagination

        return ViewSet

    _base_config = None

    @property
    def base_config(self):
        """
        Return base configuration.

        Args:
            self: (todo): write your description
        """
        if self._base_config:
            return self._base_config

        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        pages = {}
        for page in self._extra_pages:
            conf, view = self.get_page(page)
            pages[page] = conf
        for model in self._models:
            try:
                ct = get_ct(model)
            except (RuntimeError, DatabaseError):
                # This can happen before contenttypes is migrated
                ct = str(model._meta)

            if not has_perm(user, ct, 'view'):
                continue

            info = self._config[model].copy()
            info['list'] = True
            for perm in ('add', 'change', 'delete'):
                if has_perm(user, ct, perm):
                    info['can_' + perm] = True

            serializer = self.get_serializer_for_model(model)
            if not hasattr(serializer, 'get_wq_config'):
                raise Exception(model)
            conf = serializer(context={'router': self}).get_wq_config()
            for key in conf:
                if key not in info:
                    info[key] = conf[key]

            pages[info['name']] = info

        self._base_config = {'pages': pages}
        if settings.DEBUG:
            self._base_config['debug'] = True
        self._base_config.update(self._extra_config)
        return self._base_config

    def get_config(self, user=None):
        """
        Get a dict of config values.

        Args:
            self: (str): write your description
            user: (todo): write your description
        """
        if user is None or not user.is_authenticated:
            return self.base_config

        # Add user-specific permissions to configuration
        config = {
            key: val.copy() if hasattr(val, 'copy') else val
            for key, val in self.base_config.items()
        }
        for page, info in config['pages'].items():
            if not info.get('list', False):
                continue
            try:
                ct = get_ct(self._page_models[page])
            except (RuntimeError, DatabaseError):
                continue
            info = info.copy()
            for perm in ('add', 'change', 'delete'):
                if has_perm(user, ct, perm):
                    info['can_' + perm] = True
            config['pages'][page] = info

        return config

    def add_page(self, name, config, view=None):
        """
        Add a new page.

        Args:
            self: (todo): write your description
            name: (str): write your description
            config: (todo): write your description
            view: (todo): write your description
        """
        if view is None:
            class PageView(SimpleViewSet):
                template_name = name + '.html'

                def list(self, request, *args, **kwargs):
                    """
                    List all the list of configs.

                    Args:
                        self: (todo): write your description
                        request: (todo): write your description
                    """
                    return Response(config)
            view = PageView
        if 'name' not in config:
            config['name'] = name
        if 'url' not in config:
            config['url'] = name
        self._extra_pages[name] = config, view
        self._base_config = None

    def get_page(self, page):
        """
        Return the page of the given page.

        Args:
            self: (todo): write your description
            page: (str): write your description
        """
        return self._extra_pages[page]

    def get_page_config(self, name, user=None):
        """
        Get a page config value.

        Args:
            self: (todo): write your description
            name: (str): write your description
            user: (todo): write your description
        """
        config = self.get_config(user)
        return config['pages'].get(name, None)

    def get_model_config(self, model, user=None):
        """
        Get model config.

        Args:
            self: (todo): write your description
            model: (str): write your description
            user: (todo): write your description
        """
        if model in self._page_models:
            model = self._page_models[model]

        # First, check models registered with API
        if model in self._page_names:
            config = self.get_config(user)
            return config['pages'][self._page_names[model]]

        # Then check config cache directly (in case model was configured but
        # not fully registered as part of API)
        if model in self._config:
            return self._config[model]
        return None

    def model_is_registered(self, model):
        """
        Return true if the given model is registered.

        Args:
            self: (todo): write your description
            model: (todo): write your description
        """
        return model in self._models

    def get_config_view(self):
        """
        Returns the configview class based onconfig.

        Args:
            self: (todo): write your description
        """
        class ConfigView(SimpleViewSet):
            def list(this, request, *args, **kwargs):
                """
                Return a list of config values.

                Args:
                    this: (str): write your description
                    request: (todo): write your description
                """
                return Response(self.get_config(request.user))
        return ConfigView

    def get_index(self, user):
        """
        Return a list of all pages

        Args:
            self: (todo): write your description
            user: (todo): write your description
        """
        config = self.get_config(user)

        def page_sort(page):
            """
            Sort a page

            Args:
                page: (dict): write your description
            """
            is_list = page.get('list', False)
            return (not is_list, page['name'])

        pages = sorted(config['pages'].values(), key=page_sort)
        return {
            'pages': pages
        }

    def get_index_view(self):
        """
        Get the index of a given index.

        Args:
            self: (todo): write your description
        """
        class IndexView(SimpleViewSet):
            def list(this, request, *args, **kwargs):
                """
                Handles a list of users.

                Args:
                    this: (str): write your description
                    request: (todo): write your description
                """
                return Response(self.get_index(request.user))
        return IndexView

    def get_multi_view(self):
        """
        Returns a list of multiple views.

        Args:
            self: (todo): write your description
        """
        class MultipleListView(SimpleViewSet):
            def list(this, request, *args, **kwargs):
                """
                Make a list. list.

                Args:
                    this: (str): write your description
                    request: (todo): write your description
                """
                urls = request.GET.get('lists', '').split(',')
                return self.get_multi(request, urls)
        return MultipleListView

    def get_multi(self, request, urls):
        """
        Get a list of all the models.

        Args:
            self: (todo): write your description
            request: (todo): write your description
            urls: (str): write your description
        """
        conf = self.get_config(request.user)
        conf_by_url = {
            conf['url']: (page, conf)
            for page, conf
            in self.get_config(request.user)['pages'].items()
        }
        result = {}
        for listurl in urls:
            if listurl not in conf_by_url:
                continue
            page, conf = conf_by_url[listurl]
            model = self._page_models[page]
            result[listurl] = self.paginate(model, 1, request)
        return Response(result)

    def get_urls(self):
        """
        Get all registered urls.

        Args:
            self: (todo): write your description
        """
        # Register viewsets with DefaultRouter just before returning urls

        # The root viewset (with a url of "") should be registered last
        root = {}

        def register(config, viewset):
            """
            Registers the viewset to the root.

            Args:
                config: (todo): write your description
                viewset: (todo): write your description
            """
            if config['url'] == "":
                root['view'] = viewset
                root['name'] = config['name']
            else:
                self.register(config['url'], viewset, config['name'])

        # List (model) views
        for model in self._models:
            viewset = self.get_viewset_for_model(model)
            config = self._config[model]
            register(config, viewset)

        # Extra/custom viewsets
        for name in self._extra_pages:
            register(*self._extra_pages[name])

        if self.include_config_view:
            # /config.js
            self.register('config', self.get_config_view(), 'config')

        if self.include_multi_view:
            # /multi.json
            self.register('multi', self.get_multi_view(), 'multi')

        if not root:
            # default index
            self.register('', self.get_index_view(), 'index')

        urls = super(ModelRouter, self).get_urls()

        if root:
            # / - Skip registration and directly generate custom URLs
            urls.extend(self.get_root_urls(root['view'], root['name']))

        return urls

    def get_root_urls(self, viewset, name):
        """
        Return a list of urlset.

        Args:
            self: (todo): write your description
            viewset: (todo): write your description
            name: (str): write your description
        """
        lookup = self.get_lookup_regex(viewset)
        routes = self.get_routes(viewset)
        urls = []
        for route in routes:
            pattern = route.url.format(
                prefix='',
                lookup=lookup,
                trailing_slash=self.trailing_slash,
            )

            # Remove leading slash from detail view URLs
            pattern = pattern.replace('/', '', 1)

            mapping = self.get_method_map(viewset, route.mapping)
            if not mapping:
                continue
            view = viewset.as_view(mapping, **route.initkwargs)
            urls.append(url(pattern, view, name=name))

        return format_suffix_patterns(urls)

    def get_routes(self, viewset):
        """
        Return a list of routes.

        Args:
            self: (todo): write your description
            viewset: (todo): write your description
        """
        routes = super(ModelRouter, self).get_routes(viewset)
        model = getattr(viewset, "model", None)
        if not model:
            return routes

        # Custom routes

        # Re-register list view, with an additional keyword to filter this
        # model by parent models (e.g. foreign keys)

        # /[parentmodel_url]/[foreignkey_value]/[model_url]
        try:
            ct = get_ct(model)
        except (RuntimeError, DatabaseError):
            # This can happen before contenttypes is migrated
            return routes
        for pct, fields in ct.get_foreign_keys().items():
            if not pct.is_registered():
                continue
            if len(fields) > 1:
                # Multiple foreign keys to same parent model; can't
                # automatically determine which one to use
                continue
            if pct.urlbase == '':
                purlbase = ''
            else:
                purlbase = pct.urlbase + '/'
            routes.append(Route(
                url=(
                    '^' + purlbase + r'(?P<' + fields[0] +
                    r'>[^\/\?]+)/{prefix}{trailing_slash}$'
                ),
                mapping={'get': 'list'},
                name="{basename}-for-%s" % fields[0],
                detail=False,
                initkwargs={'suffix': 'List'},
            ))

        for cct in ct.get_children():
            if not cct.is_registered():
                continue
            cbase = cct.urlbase
            routes.append(Route(
                url='^%s-by-{prefix}' % cbase,
                mapping={'get': 'list'},
                name="%s-by-%s" % (cct.identifier, ct.identifier),
                detail=False,
                initkwargs={'target': cbase, 'suffix': 'List'},
            ))

        if hasattr(viewset, 'extra_routes'):
            routes += viewset.extra_routes()

        return routes

    @property
    def version(self):
        """
        Return the version number.

        Args:
            self: (todo): write your description
        """
        if not hasattr(self, '_version'):
            vtxt = getattr(settings, 'VERSION_TXT', None)
            if vtxt is None:
                self._version = None
            else:
                vfile = open(vtxt, 'r')
                self._version = vfile.read()
                vfile.close()
        return self._version

    @property
    def urls(self):
        """
        Returns a list of urls.

        Args:
            self: (todo): write your description
        """
        urls = super(ModelRouter, self).urls
        try:
            # FIXME: Remove in 2.0
            caller = inspect.stack()[1]
            code_context = getattr(caller, 'code_context', caller[4])
            if 'include' in code_context[0]:
                return urls, 'wq'
        except Exception:
            pass
        return urls, 'wq', 'wq'


# Default router instance, c.f. django.contrib.admin.sites.site
router = ModelRouter()
