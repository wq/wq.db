from django.contrib.auth.models import Group
from django.conf import settings


def assign_default_group(backend, details, response, user=None,
                         is_new=False, *args, **kwargs):

    if user is None or not is_new:
        return None

    group, created = Group.objects.get_or_create(
        name=settings.DEFAULT_AUTH_GROUP
    )
    user.groups.add(group)
    return None
