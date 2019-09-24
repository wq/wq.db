# Django settings
context_processors = (
    'django.template.context_processors.csrf',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'wq.db.rest.auth.context_processors.is_authenticated',
    'wq.db.rest.context_processors.version',
    'wq.db.rest.context_processors.router_info',
    'wq.db.rest.context_processors.wq_config',
    'wq.db.rest.context_processors.script_tags',
)

TEMPLATES = [
    {
        'BACKEND': 'django_mustache.Mustache',
        'DIRS': tuple(),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': context_processors,
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': context_processors,
        }
    }
]


SESSION_COOKIE_HTTPONLY = False

# Django Rest Framework settings
REST_FRAMEWORK = {

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.TemplateHTMLRenderer',
        'wq.db.rest.renderers.JSONRenderer',
        'wq.db.rest.renderers.GeoJSONRenderer',
    ),

    'DEFAULT_PAGINATION_CLASS': 'wq.db.rest.pagination.Pagination',
    'PAGE_SIZE': 50,

    'DEFAULT_PERMISSION_CLASSES': (
        'wq.db.rest.permissions.ModelPermissions',
    ),

    'DEFAULT_FILTER_BACKENDS': (
        'wq.db.rest.filters.FilterBackend',
    )
}

# wq.db settings
ANONYMOUS_PERMISSIONS = tuple()
SRID = 4326

# Deprecated, do not use
# FIXME: Remove in wq.db 2.0
SOCIAL_AUTH_PIPELINE = None
DEFAULT_AUTH_GROUP = None
DISAMBIGUATE = None
