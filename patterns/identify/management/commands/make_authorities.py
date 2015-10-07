from django.core.management.base import BaseCommand
from wq.db.patterns.identify.models import Authority


class Command(BaseCommand):
    def handle(self, *args, **options):
        Authority.objects.get_or_create(
            name="This Site",
        )
        Authority.objects.get_or_create(
            name="Wikipedia",
            homepage="https://wikipedia.org",
            object_url="https://wikipedia.org/wiki/%s",
        )
