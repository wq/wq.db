from rest_framework.filters import BaseFilterBackend
RESERVED_PARAMETERS = ('_', 'page', 'limit', 'format', 'slug', 'mode')

from .models import get_ct
from django.utils.six import string_types


class FilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        kwargs = {}
        for key, val in list(view.kwargs.items()) + list(request.GET.items()):
            if key in RESERVED_PARAMETERS or key in view.ignore_kwargs:
                continue
            kwargs[key] = val if isinstance(val, string_types) else val[0]
        model = getattr(view, 'model', None) or queryset.model
        ctype = get_ct(model)

        for key, val in list(kwargs.items()):
            if key in ('target',):
                del kwargs[key]
                continue
            found = False
            for f in model._meta.fields:
                if ((f.name != key and ctype.identifier + f.name != key)
                        or f.name == ctype.model):
                    continue
                found = True
                if getattr(f, 'rel', None):
                    del kwargs[key]
                    pcls = f.rel.to
                    router = getattr(view, 'router', None)
                    if router:
                        slug = router.get_lookup_for_model(pcls)
                        kwargs[f.name] = pcls.objects.get(**{slug: val})
                    elif get_ct(f.rel.to).is_identified:
                        kwargs[f.name] = pcls.objects.get_by_identifier(val)
                    else:
                        kwargs[f.name] = pcls.objects.get(pk=val)

            if not found and ctype.is_related:
                for pct in ctype.get_all_parents():
                    if pct.identifier == key:
                        pclass = pct.model_class()
                        if pct.is_identified:
                            parent = pclass.objects.get_by_identifier(
                                kwargs[key]
                            )
                        else:
                            parent = pclass.objects.get(pk=kwargs[key])
                        del kwargs[key]
                        objs = model.objects.filter_by_related(parent)
                        kwargs['pk__in'] = objs.values_list('pk', flat=True)

        return queryset.filter(**kwargs)
