from django.core.management.base import BaseCommand
from wq.db import rest
from rest_framework.utils import encoders
import json


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            default="json",
        )
        parser.add_argument(
            "--filename",
            default=None,
        )

    def handle(self, **options):
        if options.get("filename"):
            with open(options["filename"], "w") as f:
                dump_config(f, **options)
        else:
            dump_config(self.stdout, **options)


def dump_config(f, format="json", **kwargs):
    text = json.dumps(
        rest.router.config,
        cls=encoders.JSONEncoder,
        indent=4,
    )
    if format == "esm":
        text = "const config = %s;\nexport default config;" % text
    elif format == "amd":
        text = "define(%s);" % text
    f.write(text)
