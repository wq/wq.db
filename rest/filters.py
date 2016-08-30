from rest_framework.filters import BaseFilterBackend
from django.db.models.fields import FieldDoesNotExist


class FilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        kwargs = {}
        for key, val in list(view.kwargs.items()) + list(request.GET.items()):
            if key in getattr(view, 'ignore_kwargs', []):
                continue
            if isinstance(val, list):
                kwargs[key] = val[0]
            else:
                kwargs[key] = val
        model = getattr(view, 'model', None) or queryset.model

        for key, val in list(kwargs.items()):
            field_name = key.split('__')[0]
            try:
                field = model._meta.get_field(field_name)
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
            else:
                kwargs[key] = pcls.objects.get(pk=val)

        return queryset.filter(**kwargs)
