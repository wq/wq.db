from rest_framework.permissions import BasePermission
from .model_tools import get_ct


class ModelPermissions(BasePermission):
    METHOD_PERM = {
        'GET': 'view',
        'HEAD': 'view',
        'OPTIONS': 'view',
        'POST': 'add',
        'PUT': 'change',
        'PATCH': 'change',
        'DELETE': 'delete',
    }

    def has_permission(self, request, view):
        """
        Determine if the current user has the permissions.

        Args:
            self: (todo): write your description
            request: (todo): write your description
            view: (todo): write your description
        """
        if getattr(view, 'model', None) is None:
            return True
        user = request.user
        ct = get_ct(view.model)
        result = has_perm(user, ct, self.METHOD_PERM[request.method])
        return result


def has_perm(user, ct, perm):
    """
    Checks if the user has the given user.

    Args:
        user: (todo): write your description
        ct: (todo): write your description
        perm: (str): write your description
    """
    if perm == 'view':
        return True
    if isinstance(ct, str):
        perm = '%s_%s' % (ct, perm)
    else:
        perm = '%s.%s_%s' % (ct.app_label, perm, ct.model)

    if user.is_authenticated:
        return user.has_perm(perm)
    else:
        from django.conf import settings
        return perm in getattr(settings, 'ANONYMOUS_PERMISSIONS', {})
