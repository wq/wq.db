from django.utils.module_loading import autodiscover_modules
from .routers import ModelRouter, router  # NOQA


def autodiscover():
    autodiscover_modules('rest', register_to=None)
