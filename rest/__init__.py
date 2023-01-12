from django.utils.module_loading import autodiscover_modules
from .routers import ModelRouter, router
from .management.commands.dump_config import dump_config
from django.conf import settings
from rest_framework.serializers import SerializerMetaclass


__all__ = (
    "ModelSerializer",
    "ModelRouter",
    "router",
    "register",
    "autodiscover",
)


class ModelSerializer(metaclass=SerializerMetaclass):
    def __init_subclass__(cls):
        from .serializers import ModelSerializer

        cls.__bases__ = (ModelSerializer,)

    def __instancecheck__(self, instance):
        from .serializers import ModelSerializer

        return isinstance(instance, ModelSerializer)

    def __subclasscheck__(self, subclass):
        from .serializers import ModelSerializer

        return issubclass(subclass, ModelSerializer)


def autodiscover():
    autodiscover_modules("rest", register_to=None)

    if getattr(settings, "WQ_CONFIG_FILE", None):
        with open(settings.WQ_CONFIG_FILE, "w") as f:
            dump_config(f, format="esm")


def register(*models, router=router, **kwargs):
    def register_decorator(serializer):
        if hasattr(serializer, "Meta"):
            model = getattr(serializer.Meta, "model", None)
            if model and model not in models:
                models.append(model)
        for model in models:
            router.register(model, serializer=serializer, **kwargs)
        return serializer

    return register_decorator
