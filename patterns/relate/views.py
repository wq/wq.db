from rest_framework.routers import Route
from wq.db.rest.views import ModelViewSet
from wq.db.rest.models import get_ct
from .models import get_related_parents, get_related_children
from .filters import RelatedFilterBackend


class RelatedModelViewSet(ModelViewSet):
    filter_backends = ModelViewSet.filter_backends + [RelatedFilterBackend]

    def list(self, request, *args, **kwargs):
        response = super(RelatedModelViewSet, self).list(
            request, *args, **kwargs
        )
        ct = get_ct(self.model)
        for pct in get_related_parents(ct):
            self.get_parent(pct, 'related_%s' % pct.identifier, response)
        return response

    @classmethod
    def extra_routes(cls):
        routes = []
        ct = get_ct(cls.model)
        for pct in get_related_parents(ct):
            if not pct.is_registered():
                continue
            if pct.urlbase == '':
                purlbase = ''
            else:
                purlbase = pct.urlbase + '/'

            routes.append(Route(
                (
                    '^' + purlbase + r'(?P<related_' + pct.identifier +
                    '>[^\/\?]+)/{prefix}{trailing_slash}$'
                ),
                mapping={'get': 'list'},
                name="{basename}-for-related-%s" % pct.identifier,
                initkwargs={'suffix': 'List'},
            ))

        for cct in get_related_children(ct):
            if not cct.is_registered():
                continue
            cbase = cct.urlbase
            routes.append(Route(
                url='^%s-by-{prefix}' % cbase,
                mapping={'get': 'list'},
                name="%s-by-%s" % (cct.identifier, ct.identifier),
                initkwargs={'target': cbase, 'suffix': 'List'},
            ))

        return routes
