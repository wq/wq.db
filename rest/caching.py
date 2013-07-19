from django.conf import settings

if 'johnny.middleware.QueryCacheMiddleware' in settings.MIDDLEWARE_CLASSES:
    from johnny.cache import get_backend
    from johnny.settings import MIDDLEWARE_SECONDS
    jc_backend = get_backend()
else:
    jc_backend = None
    MIDDLEWARE_SECONDS = None
