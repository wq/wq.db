# Django settings
TEMPLATE_LOADERS = (
    'wq.db.rest.template.Loader',
    'django.template.loaders.app_directories.Loader',
)
SESSION_COOKIE_HTTPONLY = False

# Django Rest Framework settings
REST_FRAMEWORK = {
    'PAGINATE_BY': 50,
    'PAGINATE_BY_PARAM': 'limit',
    'DEFAULT_RENDERER_CLASSES': (
         'rest_framework.renderers.TemplateHTMLRenderer',
         'rest_framework.renderers.JSONRenderer',
         'wq.db.rest.renderers.AMDRenderer',
    ),
    'DEFAULT_MODEL_SERIALIZER_CLASS': 'wq.db.rest.serializers.ModelSerializer',
    'DEFAULT_PAGINATION_SERIALIZER_CLASS': 'wq.db.rest.serializers.PaginationSerializer',
    'DEFAULT_PERMISSION_CLASSES': (
        'wq.db.rest.permissions.ModelPermissions',
    )
}

# wq.db settings
ANONYMOUS_PERMISSIONS = {}
SRID = 3857
