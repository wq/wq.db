from django.apps import AppConfig


class RestConfig(AppConfig):
    name = 'wq.db.rest'

    def ready(self):
        """
        Determine if the module is ready.

        Args:
            self: (todo): write your description
        """
        self.module.autodiscover()
