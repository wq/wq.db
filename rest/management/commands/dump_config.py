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
        dump_config(self.stdout, **options)


def dump_config(f, format='json', **kwargs):
    text = json.dumps(
        rest.router.get_config(),
        cls=encoders.JSONEncoder,
        indent=4,
    )
    if format == "esm":
        text = "const config = %s;\nexport default config;" % text
    elif format == "amd":
        text = "define(%s);" % text
    f.write(text)
