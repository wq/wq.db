from django.core.management.base import BaseCommand
from wq.db import rest
import json
from optparse import make_option


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.option_list += (make_option(
            '--format', default='json'
        ),)

    def handle(self, *args, **options):
        rest.autodiscover()
        text = json.dumps(
            rest.router.get_config(),
            indent=4,
        )
        if options['format'] == "amd":
            text = "define(%s);" % text
        self.stdout.write(text)
