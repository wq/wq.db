from rest_framework.filters import BaseFilterBackend
RESERVED_PARAMETERS = ('_', 'page', 'limit', 'format', 'slug', 'mode')

from .models import get_ct, get_by_identifier
from django.utils.six import string_types
from django.db.models.fields import FieldDoesNotExist


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
            if key.startswith('related_'):
                continue
            field_name = key.split('__')[0]
            try:
                field = model._meta.get_field_by_name(field_name)[0]
            except FieldDoesNotExist:
                del kwargs[key]
                continue

            if field_name != key:
                continue

            rel = getattr(field, 'rel', None)
            if not rel:
                continue

            pcls = field.rel.to
            router = getattr(view, 'router', None)
            if router:
                slug = router.get_lookup_for_model(pcls)
                kwargs[key] = pcls.objects.get(**{slug: val})
            elif get_ct(pcls).is_identified:
                kwargs[key] = pcls.objects.get_by_identifier(val)
            else:
                kwargs[key] = pcls.objects.get(pk=val)

        for key, val in list(kwargs.items()):
            if key.startswith('related_') and ctype.is_related:
                for pct in ctype.get_all_parents():
                    if key == 'related_' + pct.identifier:
                        pclass = pct.model_class()
                        parent = get_by_identifier(pclass.objects, kwargs[key])
                        del kwargs[key]
                        objs = model.objects.filter_by_related(parent)
                        kwargs['pk__in'] = objs.values_list('pk', flat=True)

        return queryset.filter(**kwargs)
