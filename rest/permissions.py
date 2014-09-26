from rest_framework.permissions import BasePermission
from .models import get_ct, ContentType

# _FORBIDDEN_RESPONSE = "Sorry %s, you do not have permission to %s this %s."


class ModelPermissions(BasePermission):
    METHOD_PERM = {
        'GET': 'view',
        'HEAD': 'view',
        'POST': 'add',
        'PUT': 'change',
        'PATCH': 'change',
        'DELETE': 'delete',
    }

    def has_permission(self, request, view):
        if getattr(view, 'model', None) is None:
            return True
        user = request.user
        ct = get_ct(view.model)
        result = has_perm(user, ct, self.METHOD_PERM[request.method])
        return result


def has_perm(user, ct, perm):
    if not isinstance(ct, ContentType):
        perm = '%s_%s' % (ct, perm)
    elif perm == 'view':
        return True
    else:
        perm = '%s.%s_%s' % (ct.app_label, perm, ct.model)

    if user.is_authenticated():
        return user.has_perm(perm)
    else:
        from django.conf import settings
        return perm in getattr(settings, 'ANONYMOUS_PERMISSIONS', {})
