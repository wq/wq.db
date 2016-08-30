from django.core.management.base import BaseCommand
from wq.db import rest
import json


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            default='json',
        )

    def handle(self, **options):
        text = json.dumps(
            rest.router.get_config(),
            indent=4,
        )
        if options['format'] == "amd":
            text = "define(%s);" % text
        self.stdout.write(text)
