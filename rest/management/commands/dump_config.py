from django.core.management.base import NoArgsCommand
from wq.db import rest
import json


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        rest.autodiscover()
        self.stdout.write(
            json.dumps(
                rest.router.get_config(),
                indent=4,
            )
        )
