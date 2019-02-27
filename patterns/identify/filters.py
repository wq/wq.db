from rest_framework.filters import BaseFilterBackend
from .models import Identifier


class IdentifierFilterBackend(BaseFilterBackend):
    ignore_extra = True
    exclude_apps = []
    view_kwarg = 'ids'

    @property
    def filter_options(self):
        if hasattr(self, '_filter_options'):
            return self._filter_options

        slugs = self.view.kwargs[self.view_kwarg].split('/')
        id_map, unresolved = Identifier.objects.resolve(
            slugs, exclude_apps=self.exclude_apps
        )
        options = {}
        if unresolved:
            options['extra'] = []
            for key, items in unresolved.items():
                items = [
                    item for item in items
                    if self.can_filter(item.content_type.model)
                ]
                if len(items) > 1:
                    raise Exception(
                        "Could not resolve %s to a single item!" % key
                    )
                elif len(items) == 1:
                    if id_map is None:
                        id_map = {}
                    id_map[key] = items[0]
                else:
                    options['extra'].append(key)

        if id_map:
            for slug, ident in id_map.items():
                ctype = ident.content_type.model
                if ctype not in options:
                    options[ctype] = []
                options[ctype].append(ident)

        self._filter_options = options
        return options

    def filter_queryset(self, request, queryset, view):
        self.request = request
        self.view = view

        # Filter by identifiers in url
        for name, idents in self.filter_options.items():
            if name == "extra":
                continue
            ids = [ident.object_id for ident in idents]
            fn = self.get_filter_by(name)
            if fn:
                queryset = fn(queryset, ids)
            else:
                raise Exception("Don't know how to filter by %s" % name)

        # Filter by any extra slugs in url
        if 'extra' in self.filter_options:
            fn = getattr(self.view, 'filter_by_extra', self.filter_by_extra)
            queryset = fn(queryset, self.filter_options['extra'])

        return queryset

    def get_filter_by(self, name):
        fn = getattr(self, 'filter_by_%s' % name, None)
        if not fn:
            fn = getattr(self.view, 'filter_by_%s' % name, None)
        return fn

    def can_filter(self, name):
        return self.get_filter_by(name) is not None

    def filter_by_extra(self, queryset, extra):
        if self.ignore_extra:
            return queryset
        else:
            raise Exception("Extra URL options found: %s" % extra)
