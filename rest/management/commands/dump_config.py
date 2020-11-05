from django.core.management.base import BaseCommand
from wq.db import rest
from rest_framework.utils import encoders
import json


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        Add command line arguments.

        Args:
            self: (todo): write your description
            parser: (todo): write your description
        """
        parser.add_argument(
            '--format',
            default='json',
        )

    def handle(self, **options):
        """
        Handle command.

        Args:
            self: (todo): write your description
            options: (todo): write your description
        """
        text = json.dumps(
            rest.router.get_config(),
            cls=encoders.JSONEncoder,
            indent=4,
        )
        if options['format'] == "esm":
            text = "export default %s;" % text
        elif options['format'] == "amd":
            text = "define(%s);" % text
        self.stdout.write(text)
