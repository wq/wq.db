from django.contrib.contenttypes.models import ContentType
from wq.db.models import AnnotatedModel, IdentifiedModel

_FORBIDDEN_APPS = ('auth','sessions','admin','contenttypes','reversion','south')

def get_ct(cls):
    return ContentType.objects.get_for_model(cls)

def get_id(contenttype):
    if contenttype is None:
        return 'NONE'
    return contenttype.name.replace(' ', '')

def geturlbase(ct):
    cls = ct.model_class()
    return getattr(cls, 'slug', get_id(ct) + 's')

def has_perm(user, ct, perm):
    if not isinstance(ct, ContentType):
        perm = '%s_%s' % (ct, perm)
    elif ct.app_label in _FORBIDDEN_APPS and not user.is_superuser:
        return False
    elif perm == 'view':
        return True
    else:
        perm = '%s.%s_%s' % (ct.app_label, ct.model, perm)

    if user.is_authenticated():
        return user.has_perm(perm)
    else:
        from django.conf import settings
        return perm in getattr(settings, 'ANONYMOUS_PERMISSIONS', {})

def get_config(user):
     pages = {}
     for ct in ContentType.objects.all():
         if not has_perm(user, ct, 'view'):
             continue
         cls = ct.model_class()
         if cls is None:
             continue
         info = {'name': ct.name, 'url': geturlbase(ct), 'list': True, 'parents': [], 'children': []}
         for perm in ('add', 'change', 'delete'):
             if has_perm(user, ct, perm):
                 info['can_' + perm] = True
         for f in cls._meta.fields:
             if f.rel is not None and type(f.rel).__name__ == 'ManyToOneRel':
                 pct = get_ct(f.rel.to)
                 info['parents'].append(get_id(pct))

         for r in cls._meta.get_all_related_objects():
             cct = get_ct(r.model)
             info['children'].append(get_id(cct))

         info['annotated'] = issubclass(cls, AnnotatedModel)
         info['identified'] = issubclass(cls, IdentifiedModel)
         pages[get_id(ct)] = info
     return {'pages': pages}
