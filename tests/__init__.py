import os
from django.test.utils import setup_test_environment
import django
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
setup_test_environment()
django.setup()

if getattr(django.conf.settings, "VARIANT") == "spatialite":
    # See https://code.djangoproject.com/ticket/32935
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT InitSpatialMetaData(1);")
    connection.close()

call_command("makemigrations", interactive=False)
call_command("migrate", interactive=False)
