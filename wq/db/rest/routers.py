from django.utils.encoding import force_str
from django.urls import re_path, path

from django.conf import settings
from rest_framework.routers import DefaultRouter, Route
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.settings import api_settings
from rest_framework.response import Response

from .permissions import has_perm
from .views import SimpleViewSet, ModelViewSet
from .renderers import JSONRenderer, ESMRenderer
from .exceptions import ImproperlyConfigured
from .maps import (
    tiles,
    update_tiles_url,
    update_geometry_fields,
    update_map_config,
)


class ModelRouter(DefaultRouter):
    _models = set()
    _serializers = {}
    _nested_arrays = {}
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
    include_tiles_view = True

    default_serializer_class = None

    def __init__(self, trailing_slash=False):
        # Add trailing slash for HTML list views
        self.routes.append(
            Route(
                url=r"^{prefix}/$",
                mapping={"get": "list", "post": "create"},
                name="{basename}-list",
                detail=False,
                initkwargs={"suffix": "List"},
            )
        )
        super(ModelRouter, self).__init__(trailing_slash=trailing_slash)

    def register(self, model, *args, **kwargs):
        if isinstance(model, type) and not args:
            self.register_model(model, **kwargs)
        else:
            super().register(model, *args, **kwargs)

    def register_model(
        self,
        model,
        viewset=None,
        serializer=None,
        nested_arrays=None,
        fields=None,
        queryset=None,
        filter=None,
        cache_filter=None,
        **kwargs,
    ):
        if isinstance(model, str) and "." in model:
            from django.db.models import get_model

            model = get_model(*model.split("."))

        if viewset:
            self.register_viewset(model, viewset)
        if queryset is not None:
            self.register_queryset(model, queryset)
        if filter:
            self.register_filter(model, filter)
        if cache_filter:
            self.register_cache_filter(model, cache_filter)
            kwargs.setdefault("cache", "filter")

        if "name" not in kwargs:
            kwargs["name"] = model._meta.model_name
        if "url" not in kwargs:
            url = force_str(model._meta.verbose_name_plural)
            kwargs["url"] = url.replace(" ", "")

        other_model = self._page_models.get(kwargs["name"], None)
        if other_model:
            raise ImproperlyConfigured(
                "Could not register %s: "
                "the name '%s' was already registered for %s"
                % (model, kwargs["name"], other_model)
            )

        other_model = self._url_models.get(kwargs["url"], None)
        if other_model:
            raise ImproperlyConfigured(
                "Could not register %s: "
                "the url '%s' was already registered for %s"
                % (model, kwargs["url"], other_model)
            )

        self.register_config(model, kwargs)

        if serializer:
            self.register_serializer(model, serializer)

        if nested_arrays:
            if not isinstance(nested_arrays, (list, tuple)):
                nested_arrays = [nested_arrays]
            self._nested_arrays[model] = nested_arrays

        if fields:
            self.register_fields(model, fields)

        self._models.add(model)
        self._page_names[model] = kwargs["name"]
        self._page_models[kwargs["name"]] = model
        self._url_models[kwargs["url"]] = model

    def register_viewset(self, model, viewset):
        self._viewsets[model] = viewset

    def register_serializer(self, model, serializer):
        self._serializers[model] = serializer
        self._base_config = None

    def register_fields(self, model, fields):
        self._fields[model] = fields

    def register_queryset(self, model, queryset):
        self._querysets[model] = queryset

    def register_filter(self, model, filter):
        self._filters[model] = filter

    def register_cache_filter(self, model, cache_filter):
        self._cache_filters[model] = cache_filter

    def register_config(self, model, config):
        for key in ("partial", "reversed", "max_local_pages"):
            if key in config:
                raise ImproperlyConfigured(
                    '"%s" is deprecated in favor of "cache"' % key
                )
        self._config[model] = config
        self._base_config = None

    def update_config(self, model, **kwargs):
        if model not in self._config:
            raise RuntimeError("%s must be registered first" % model)
        for key in ("partial", "reversed", "max_local_pages"):
            if key in kwargs:
                raise ImproperlyConfigured(
                    '"%s" is deprecated in favor of "cache"' % key
                )
        self._config[model].update(kwargs)
        self._base_config = None

    def set_extra_config(self, **extra):
        self._extra_config.update(extra)
        self._base_config = None

    def get_default_serializer_class(self, model_class=None):
        if not self.default_serializer_class:
            from .serializers import ModelSerializer

            self.default_serializer_class = ModelSerializer
        return self.default_serializer_class

    def get_class(self, classes, model_class, default=lambda model: None):
        if model_class in classes:
            return classes[model_class]
        else:
            # Make sure we're not dealing with a proxy
            real_model = model_class._meta.concrete_model
            if real_model in classes:
                return classes[real_model]
            else:
                return default(real_model)

    def get_serializer_for_model(self, model_class, serializer_depth=None):
        serializer = self.get_class(
            self._serializers, model_class, self.get_default_serializer_class
        )

        meta = getattr(serializer, "Meta", object)
        if not getattr(meta, "model", None):
            if getattr(meta, "fields", None) or getattr(meta, "exclude", None):
                include_fields = None
            else:
                include_fields = self._fields.get(model_class, None)
                if not include_fields:
                    raise ImproperlyConfigured(
                        "No serializer fields defined for %s" % model_class
                    )
            serializer = serializer.for_model(
                model_class,
                include_fields=include_fields,
                serializer_depth=serializer_depth,
                nested_arrays=self._nested_arrays.get(model_class),
            )

        meta = getattr(serializer, "Meta", object)
        conf = self._config.get(model_class, None)
        if not conf:
            conf = self._config.get(model_class._meta.concrete_model, None)

        if conf:
            wq_conf = getattr(meta, "wq_config", {}).copy()
            wq_conf.update(conf)
            meta.wq_config = wq_conf
            serializer.Meta = meta

        return serializer

    def serialize(self, obj, many=False, depth=None, request=None):
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
        context = {"router": self}
        if request:
            context["request"] = request
        return serializer(obj, many=many, context=context).data

    def get_object_id(self, instance):
        return getattr(instance, self.get_lookup_for_model(instance))

    def get_by_identifier(self, queryset, ident):
        if hasattr(queryset, "get_by_identifier"):
            return queryset.get_by_identifier(ident)
        else:
            lookup = self.get_lookup_for_model(queryset.model)
            return queryset.get(**{lookup: ident})

    def get_paginate_by_for_model(self, model_class):
        config = self.get_model_config(model_class) or {}
        paginate_by = config.get("per_page", None)
        if paginate_by:
            return paginate_by
        return api_settings.PAGE_SIZE

    def paginate(self, model, page_num, request):
        # FIXME: should copy() before modifying but doing so causes recursion
        request.GET = {
            "page": page_num,
        }
        view = self.get_viewset_for_model(model).as_view(
            actions={"get": "list"},
        )
        return view(request._request).data

    def get_queryset_for_model(self, model, request=None):
        if model in self._page_models:
            model = self._page_models[model]
        if model in self._querysets:
            qs = self._querysets[model]
        else:
            qs = model.objects.all()
        if request:
            if model in self._filters:
                qs = self._filters[model](qs, request)
            config = self.get_model_config(model) or {}
            renderer = getattr(request, "accepted_renderer", None)
            if (
                config.get("defer_geometry")
                and config.get("geometry_fields")
                and renderer
                and renderer.format != "geojson"
            ):
                qs = qs.defer(
                    *[
                        field["name"]
                        for field in config["geometry_fields"]
                        if "." not in field["name"]
                    ]
                )
        return qs

    def get_cache_filter_for_model(self, model):
        return self._cache_filters.get(model, lambda qs, req: qs.none())

    def get_lookup_for_model(self, model_class):
        config = self.get_model_config(model_class) or {}
        return config.get("lookup", "pk")

    def get_viewset_for_model(self, model_class):
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

    def get_base_url(self):
        return getattr(settings, "WQ_BASE_URL", "")

    _base_config = None

    @property
    def base_config(self):
        if self._base_config:
            return self._base_config

        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()
        pages = {}
        for page in self._extra_pages:
            conf, view = self.get_page(page)
            pages[page] = conf.copy()
        for model in self._models:
            if not has_perm(user, model, "view"):
                continue

            info = self._config[model].copy()
            info["list"] = True
            for perm in ("add", "change", "delete"):
                if has_perm(user, model, perm):
                    info["can_" + perm] = True

            serializer = self.get_serializer_for_model(model)
            if not hasattr(serializer, "get_wq_config"):
                raise Exception(model)
            conf = serializer(context={"router": self}).get_wq_config()
            for key in conf:
                if key not in info:
                    info[key] = conf[key]

            pages[info["name"]] = info

        site_title = getattr(settings, "PROJECT_NAME", None)
        base_url = self.get_base_url()

        if not any(conf.get("url") == "" for conf in pages.values()):
            pages.setdefault(
                "index",
                {
                    "url": "",
                    "name": "index",
                    "show_in_index": False,
                    "verbose_name": site_title,
                    "map": True,
                },
            )

        for conf in pages.values():
            update_geometry_fields(conf)

        for conf in pages.values():
            update_map_config(conf, pages)

        self._base_config = {
            "pages": pages,
            "site_title": site_title,
            "router": {"base_url": base_url},
            "store": {
                "service": base_url,
                "defaults": {"format": "json"},
            },
        }
        if getattr(settings, "WQ_CONFIG", None):
            self._base_config.update(settings.WQ_CONFIG)

        update_tiles_url(self._base_config.get("map"), self.get_base_url())

        if settings.DEBUG:
            self._base_config["debug"] = True
        self._base_config.update(self._extra_config)
        return self._base_config

    @property
    def config(self):
        return self.base_config

    def get_user_config(self, user):
        # Add user-specific permissions to configuration
        config = {"pages": {}}
        for page, info in self.config["pages"].items():
            if not info.get("list", False):
                continue
            model = self._page_models[page]
            perms = {}
            for perm in ("add", "change", "delete"):
                if has_perm(user, model, perm):
                    perms["can_" + perm] = True
            config["pages"][page] = perms

        return config

    def add_page(self, name, config, view=None):
        if view is None:

            class PageView(SimpleViewSet):
                template_name = name + ".html"

                def list(self, request, *args, **kwargs):
                    return Response(config)

            view = PageView
        if "name" not in config:
            config["name"] = name
        if "url" not in config:
            config["url"] = name
        self._extra_pages[name] = config, view
        self._base_config = None

    def get_page(self, page):
        return self._extra_pages[page]

    def get_page_config(self, name):
        return self.config["pages"].get(name, None)

    def get_model_config(self, model):
        if not isinstance(model, type):
            model = type(model)
        if model in self._page_models:
            model = self._page_models[model]

        # First, check models registered with API
        if model in self._page_names:
            return self.config["pages"][self._page_names[model]]

        # Then check config cache directly (in case model was configured but
        # not fully registered as part of API)
        if model in self._config:
            return self._config[model]
        return None

    def model_is_registered(self, model):
        return model in self._models

    def get_foreign_keys(self, model):
        rel_models = {}
        for f in model._meta.fields:
            rel = f.remote_field
            if (
                rel is not None
                and type(rel).__name__ == "ManyToOneRel"
                and self.model_is_registered(rel.model)
            ):
                rel_models.setdefault(rel.model, [])
                rel_models[rel.model].append(f.name)
        return rel_models

    def get_config_view(self):
        class ConfigView(SimpleViewSet):
            renderer_classes = [JSONRenderer, ESMRenderer]

            def list(this, request, *args, **kwargs):
                return Response(self.config)

        return ConfigView

    def get_index_view(self):
        class IndexView(SimpleViewSet):
            def list(this, request, *args, **kwargs):
                return Response({})

        return IndexView

    def get_multi_view(self):
        class MultipleListView(SimpleViewSet):
            def list(this, request, *args, **kwargs):
                urls = request.GET.get("lists", "").split(",")
                return self.get_multi(request, urls)

        return MultipleListView

    def get_multi(self, request, urls):
        conf_by_url = {
            conf["url"]: (page, conf)
            for page, conf in self.config["pages"].items()
        }
        result = {}
        for listurl in urls:
            if listurl not in conf_by_url:
                continue
            page, conf = conf_by_url[listurl]
            model = self._page_models[page]
            result[listurl] = self.paginate(model, 1, request)
        return Response(result)

    def tiles(self, request, z, x, y):
        return tiles(self, request, z, x, y)

    def get_urls(self):
        # Register viewsets with DefaultRouter just before returning urls

        # The root viewset (with a url of "") should be registered last
        root = {}

        def register(config, viewset):
            if config["url"] == "":
                root["view"] = viewset
                root["name"] = config["name"]
            else:
                self.register(config["url"], viewset, config["name"])

        # List (model) views
        for model in self._models:
            viewset = self.get_viewset_for_model(model)
            config = self._config[model]
            register(config, viewset)

        # Extra/custom viewsets
        for name, (config, viewset) in self._extra_pages.items():
            if not config.get("external"):
                register(config, viewset)

        if self.include_config_view:
            # /config.js
            self.register("config", self.get_config_view(), "config")

        if self.include_multi_view:
            # /multi.json
            self.register("multi", self.get_multi_view(), "multi")

        if not root:
            # default index
            self.register("", self.get_index_view(), "index")

        urls = super(ModelRouter, self).get_urls()

        if root:
            # / - Skip registration and directly generate custom URLs
            urls.extend(self.get_root_urls(root["view"], root["name"]))

        if self.include_tiles_view:
            urls.append(path("tiles/<int:z>/<int:x>/<int:y>.pbf", self.tiles))

        return urls

    def get_root_urls(self, viewset, name):
        lookup = self.get_lookup_regex(viewset)
        routes = self.get_routes(viewset)
        urls = []
        for route in routes:
            pattern = route.url.format(
                prefix="",
                lookup=lookup,
                trailing_slash=self.trailing_slash,
            )

            # Remove leading slash from detail view URLs
            pattern = pattern.replace("/", "", 1)

            mapping = self.get_method_map(viewset, route.mapping)
            if not mapping:
                continue
            view = viewset.as_view(mapping, **route.initkwargs)
            urls.append(re_path(pattern, view, name=name))

        return format_suffix_patterns(urls)

    def get_routes(self, viewset):
        routes = super(ModelRouter, self).get_routes(viewset)
        model = getattr(viewset, "model", None)
        if not model:
            return routes

        # Custom routes

        # Re-register list view, with an additional keyword to filter this
        # model by parent models (e.g. foreign keys)

        # /[parentmodel_url]/[foreignkey_value]/[model_url]
        for rel_model, fields in self.get_foreign_keys(model).items():
            if len(fields) > 1:
                # Multiple foreign keys to same parent model; can't
                # automatically determine which one to use
                continue
            purlbase = self.get_model_config(rel_model)["url"]
            if purlbase != "":
                purlbase += "/"
            routes.append(
                Route(
                    url=(
                        "^"
                        + purlbase
                        + r"(?P<"
                        + fields[0]
                        + r">[^\/\?]+)/{prefix}{trailing_slash}$"
                    ),
                    mapping={"get": "list"},
                    name="{basename}-for-%s" % fields[0],
                    detail=False,
                    initkwargs={"suffix": "List"},
                )
            )

        if hasattr(viewset, "extra_routes"):
            routes += viewset.extra_routes()

        return routes

    @property
    def version(self):
        if not hasattr(self, "_version"):
            vtxt = getattr(settings, "VERSION_TXT", None)
            if vtxt is None:
                self._version = None
            else:
                vfile = open(vtxt, "r")
                self._version = vfile.read()
                vfile.close()
        return self._version

    @property
    def urls(self):
        urls = super(ModelRouter, self).urls
        return urls, "wq", "wq"


# Default router instance, c.f. django.contrib.admin.sites.site
router = ModelRouter()
