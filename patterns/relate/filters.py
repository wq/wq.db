from rest_framework.filters import BaseFilterBackend

from wq.db.rest.models import get_ct, get_by_identifier
from .models import get_related_parents


class RelatedFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        ctype = get_ct(view.model)
        filter = {}
        for key, val in list(view.kwargs.items()) + list(request.GET.items()):
            if not key.startswith('related_'):
                continue
            if isinstance(val, list):
                val = val[0]
            for pct in get_related_parents(ctype):
                if key == 'related_' + pct.identifier:
                    pclass = pct.model_class()
                    parent = get_by_identifier(pclass.objects, val)
                    objs = view.model.objects.filter_by_related(parent)
                    filter['pk__in'] = objs.values_list('pk', flat=True)
        return queryset.filter(**filter)
