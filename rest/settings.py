REST_FRAMEWORK = {
    'PAGINATE_BY_PARAM': 'limit',
    'DEFAULT_RENDERER_CLASSES': (
         'rest_framework.renderers.TemplateHTMLRenderer',
         'rest_framework.renderers.JSONRenderer',
         'wq.db.rest.renderers.AMDRenderer',
    )
}
TEMPLATE_LOADERS = (
    'wq.db.rest.template.Loader',
    'django.template.loaders.app_directories.Loader',
)
