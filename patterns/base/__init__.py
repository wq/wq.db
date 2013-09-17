from django.contrib.contenttypes.generic import GenericRelation
from south.modelsinspector import add_ignored_fields
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


# Trick rest_framework into serializing these relationships
class SerializableGenericRelation(GenericRelation):
    def __init__(self, *args, **kwargs):
        super(SerializableGenericRelation, self).__init__(*args, **kwargs)
        self.serialize = True

add_ignored_fields(["^wq.db.patterns.base.SerializableGenericRelation"])


# Utility for determining whether models have been swapped
class Swapper(object):
    def swappable_setting(self, app_label, model):
        if app_label == 'auth' and model == 'User':
            return 'AUTH_USER_MODEL'
        return 'WQ_%s_MODEL' % model.upper()

    def is_swapped(self, app_label, model):
        default_model = "%s.%s" % (app_label, model)
        setting = self.swappable_setting(app_label, model)
        value = getattr(settings, setting, default_model)
        if value != default_model:
            return value
        else:
            return False

    def get_swapped_models(self, app_label, models):
        return {
            model: self.is_swapped(app_label, model)
            for model in models
        }

    def load_model(self, app_label, model, orm=None, required=True):
        swapped = self.is_swapped(app_label, model)
        if swapped:
            app_label, model = swapped.split('.')
        else:
            if orm is not None:
                return orm['%s.%s' % (app_label, model)]

        from django.db.models import get_model
        cls = get_model(app_label, model)
        if cls is None and required:
            raise ImproperlyConfigured(
                "Could not find %s.%s!" % (app_label, model)
            )
        return cls

swapper = Swapper()
