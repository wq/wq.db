from django.utils.module_loading import autodiscover_modules
from .routers import ModelRouter, router


__all__ = (
    "ModelRouter",
    "router",
    "autodiscover",
    "default_app_config",
)


def autodiscover():
    """
    Registers autodiscover modules.

    Args:
    """
    autodiscover_modules('rest', register_to=None)


default_app_config = 'wq.db.rest.apps.RestConfig'
