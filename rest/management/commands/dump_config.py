from django.core.management.base import NoArgsCommand
from wq.db.rest import app
import json


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        app.autodiscover()
        json.dump(
            self.stdout,
            app.router.get_config(),
            indent=4,
        )
