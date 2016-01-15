from django.utils.six import string_types


def get_ct(model, for_concrete_model=False):
    from .models import ContentType
    if isinstance(model, string_types):
        ctype = ContentType.objects.get_by_identifier(model)
    else:
        ctype = ContentType.objects.get_for_model(
            model, for_concrete_model=for_concrete_model
        )
        # get_for_model sometimes returns a DjangoContentType - caching issue?
        if not isinstance(ctype, ContentType):
            ctype = ContentType.objects.get(pk=ctype.pk)
            ContentType.objects._add_to_cache(ContentType.objects.db, ctype)
    return ctype


def get_object_id(instance):
    ct = get_ct(instance)
    config = ct.get_config()
    if config and 'lookup' in config:
        return getattr(instance, config['lookup'])
    return instance.pk


def get_by_identifier(queryset, ident):
    if hasattr(queryset, 'get_by_identifier'):
        return queryset.get_by_identifier(ident)
    else:
        ct = get_ct(queryset.model)
        config = ct.get_config()
        if config and 'lookup' in config:
            lookup = config['lookup']
        else:
            lookup = 'pk'
        return queryset.get(**{lookup: ident})
