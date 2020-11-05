from django.core.management.base import BaseCommand
from wq.db.patterns.identify.models import Authority


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Create or create request.

        Args:
            self: (todo): write your description
            options: (todo): write your description
        """
        Authority.objects.get_or_create(
            name="This Site",
        )
        Authority.objects.get_or_create(
            name="Wikipedia",
            homepage="https://wikipedia.org",
            object_url="https://wikipedia.org/wiki/%s",
        )
