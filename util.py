from django.contrib.contenttypes.models import ContentType
from wq.db.models import AnnotatedModel, IdentifiedModel, RelatedModel, RelationshipType

_FORBIDDEN_APPS = ('auth','sessions','admin','contenttypes','reversion','south')

def get_ct(cls):
    return ContentType.objects.get_for_model(cls)

def get_id(contenttype):
    if contenttype is None:
        return 'NONE'
    return contenttype.name.replace(' ', '')

def get_object_id(instance):
    if issubclass(type(instance), IdentifiedModel):
        ids = instance.identifiers.filter(is_primary=True)
        if len(ids) > 0:
            return ids[0].slug
    return instance.pk

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

# Get foreign keys for this content type
def get_parents(ct):
    cls = ct.model_class()
    if cls is None:
        return []
    parents = []
    for f in cls._meta.fields:
        if f.rel is not None and type(f.rel).__name__ == 'ManyToOneRel':
            parents.append(get_ct(f.rel.to))
    return parents

# Get foreign keys and RelationshipType parents for this content type
def get_all_parents(ct):
    parents = get_parents(ct)
    cls = ct.model_class()
    if issubclass(cls, RelatedModel):
        for rtype in RelationshipType.objects.filter(to_type=ct):
            parents.append(rtype.from_type)
    return parents

def get_children(ct):
    cls = ct.model_class()
    if cls is None:
        return [];
    return [get_ct(r.model) for r in cls._meta.get_all_related_objects()]

def get_all_children(ct):
    children = get_children(ct)
    cls = ct.model_class()
    if issubclass(cls, RelatedModel):
        for rtype in RelationshipType.objects.filter(from_type=ct):
            children.append(rtype.to_type)
    return children

def get_config(user):
     from django.conf import settings
     if hasattr(settings, 'REST_CONFIG'):
         return settings.REST_CONFIG
     pages = {}
     pages['login']  = {'name': 'Log in',  'url': 'login'}
     pages['logout'] = {'name': 'Log out', 'url': 'logout'}
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

         for pct in get_parents(ct):
             if has_perm(user, pct, 'view'):
                 info['parents'].append(get_id(pct))

         for cct in get_children(ct):
             if has_perm(user, cct, 'view'):
                 info['children'].append(get_id(cct))

         info['annotated'] = issubclass(cls, AnnotatedModel)
         info['identified'] = issubclass(cls, IdentifiedModel)
         pages[get_id(ct)] = info
     return {'pages': pages}

def user_dict(user):
    u = {
        key: getattr(user, key)
        for key in ('username', 'first_name', 'last_name', 'email', 
                    'is_active', 'is_staff', 'is_superuser')
    }
    if hasattr(user, 'social_auth'):
        auth = user.social_auth.all()
        if auth.count() > 0:
            u['social_auth'] = True
            u['accounts'] = [{
                'provider_id':    unicode(a.provider),
                'provider_label': a.provider.title(),
                'id':             a.pk,
                'label':          a.uid
            } for a in auth]
    return u

class MultiQuerySet(object):
    querysets = []
    def __init__(self, *args, **kwargs):
        self.querysets = args

    def __getitem__(self, index):
        if isinstance(index, slice):
            multi = True
        else:
            multi = False
            index = slice(index, index + 1)
        
        result = []
        for qs in self.querysets:
             if index.start < qs.count():
                 result.extend(qs[index])
             index = slice(index.start - qs.count(),
                           index.stop  - qs.count())
             if index.start < 0:
                 if index.stop < 0:
                     break
                 index = slice(0, index.stop)
        if multi:
            return (item for item in result)
        else:
            return result[0]

    def __iter__(self):
        for qs in self.querysets:
            for item in qs:
                yield item

    def count(self):
        result = 0
        for qs in self.querysets:
            result += qs.count()
        return result
