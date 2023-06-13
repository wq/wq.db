from rest_framework.permissions import BasePermission


class ModelPermissions(BasePermission):
    METHOD_PERM = {
        "GET": "view",
        "HEAD": "view",
        "OPTIONS": "view",
        "POST": "add",
        "PUT": "change",
        "PATCH": "change",
        "DELETE": "delete",
    }

    def has_permission(self, request, view):
        if getattr(view, "model", None) is None:
            return True
        user = request.user
        method_perm = self.METHOD_PERM.get(
            request.method, self.METHOD_PERM["GET"]
        )
        return has_perm(user, view.model, method_perm)


def has_perm(user, model, method_perm):
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    perm = f"{app_label}.{method_perm}_{model_name}"

    if method_perm == "view":
        return True
    elif user.is_authenticated:
        return user.has_perm(perm)
    else:
        from django.conf import settings

        return perm in getattr(settings, "ANONYMOUS_PERMISSIONS", {})
