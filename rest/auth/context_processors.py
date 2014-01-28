from wq.db.rest import app
from django.middleware import csrf


def is_authenticated(request):
    # FIXME: Pystache contexts aren't working with Django 1.6 SimpleLazyObject
    # due to iter(data) not failing.  This makes it difficult to use {{user}}
    # in Mustache templates.  We could just override the user context variable,
    # but that will likely break Django templates, such as those used in
    # contrib.admin.  Instead, the workaround is to define "user" only within
    # the is_authenticated context.
    #
    # In Mustache templates, always use:
    #   {{#is_authenticated}}{{user.username}}{{/is_authenticated}}
    # In Django templates, just use:
    #   {{user.username}}

    if request.user.is_authenticated():
        return {
            'is_authenticated': {'user': app.router.serialize(request.user)}
        }
    else:
        return {'is_authenticated': False}


def social_auth(request):
    if (not request.user.is_authenticated()
            or not hasattr(request.user, 'social_auth')
            or request.user.social_auth.count() == 0):
        return {}

    return {
        'social_auth': {
            'accounts': [
                app.router.serialize(auth)
                for auth in request.user.social_auth.all()
            ]
        }
    }


def csrftoken(request):
    return {
        'csrftoken': csrf.get_token(request)
    }
