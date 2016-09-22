from django.core.management.base import BaseCommand
from wq.db import rest
from rest_framework.utils import encoders
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
            cls=encoders.JSONEncoder,
            indent=4,
        )
        if options['format'] == "amd":
            text = "define(%s);" % text
        self.stdout.write(text)
