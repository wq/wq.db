from django.apps import AppConfig


class RestConfig(AppConfig):
    name = 'wq.db.rest'

    def ready(self):
        self.module.autodiscover()
