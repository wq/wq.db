from django.utils.module_loading import autodiscover_modules
from .routers import ModelRouter, router
from .management.commands.dump_config import dump_config
from django.conf import settings


__all__ = (
    "ModelRouter",
    "router",
    "autodiscover",
    "default_app_config",
)


def autodiscover():
    autodiscover_modules('rest', register_to=None)

    if getattr(settings, 'WQ_CONFIG_FILE', None):
        with open(settings.WQ_CONFIG_FILE, 'w') as f:
            dump_config(f, format='esm')


default_app_config = 'wq.db.rest.apps.RestConfig'
