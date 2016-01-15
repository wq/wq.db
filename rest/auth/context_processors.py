from wq.db import rest


def is_authenticated(request):
    return {
        'is_authenticated': request.user.is_authenticated()
    }


def social_auth(request):
    if (not request.user.is_authenticated() or
            not hasattr(request.user, 'social_auth') or
            request.user.social_auth.count() == 0):
        return {}

    user = rest.router.serialize(request.user)
    return {
        'social_auth': user.get('social_auth', {})
    }
