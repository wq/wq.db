import os

from wq.db.default_settings import (  # NOQA
    TEMPLATES,
    REST_FRAMEWORK,
    SRID,
)

SECRET_KEY = '1234'

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'wq.db.rest',
    'wq.db.rest.auth',
    'wq.db.patterns.identify',
    'tests.rest_app',
    'tests.conflict_app',
    'tests.patterns_app',
    'tests.naturalkey_app',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'wqdb_test',
        'USER': 'postgres',
    }
}

USE_TZ = True
TIME_ZONE = "America/Chicago"

ROOT_URLCONF = "tests.urls"
BASE_DIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
VERSION_TXT = os.path.join(BASE_DIR, "version.txt")

TEMPLATES[0]['DIRS'] += (os.path.join(BASE_DIR, "templates"),)
