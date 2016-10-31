# Django settings
context_processors = (
    'django.template.context_processors.csrf',
    'django.contrib.auth.context_processors.auth',
    'wq.db.rest.auth.context_processors.is_authenticated',
    'wq.db.rest.auth.context_processors.social_auth',
    'wq.db.rest.context_processors.version',
    'wq.db.rest.context_processors.router_info',
    'wq.db.rest.context_processors.wq_config',
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

    'DEFAULT_PERMISSION_CLASSES': (
        'wq.db.rest.permissions.ModelPermissions',
    ),

    'DEFAULT_FILTER_BACKENDS': (
        'wq.db.rest.filters.FilterBackend',
    )
}

# Django Social Auth settings
SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
    'wq.db.rest.auth.pipeline.assign_default_group',
)

# wq.db settings
ANONYMOUS_PERMISSIONS = tuple()
SRID = 4326
DEFAULT_AUTH_GROUP = "Users"
DISAMBIGUATE = True
