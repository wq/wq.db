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

WITH_GIS = os.environ.get("WITH_GIS")

if WITH_GIS:
    INSTALLED_APPS += ('tests.gis_app',)


WITH_NONROOT = os.environ.get("WITH_NONROOT")


if os.environ.get('PSYCOPG2'):
    if WITH_GIS:
        engine = 'django.contrib.gis.db.backends.postgis'
    else:
        engine = 'django.db.backends.postgresql'
    DATABASES = {
        'default': {
            'ENGINE': engine,
            'NAME': 'wqdb_test',
            'USER': 'postgres',
        }
    }
else:
    if WITH_GIS:
        engine = 'django.contrib.gis.db.backends.spatialite'
        SPATIALITE_LIBRARY_PATH = 'mod_spatialite.so'
    else:
        engine = 'django.db.backends.sqlite3'
    DATABASES = {
        'default': {
             'ENGINE': engine,
             'NAME': 'wqdb_test.sqlite3',
        }
    }

USE_TZ = True
TIME_ZONE = "America/Chicago"

ROOT_URLCONF = "tests.urls"
BASE_DIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
VERSION_TXT = os.path.join(BASE_DIR, "version.txt")
WQ_SCRIPT_FILE = os.path.join(BASE_DIR, "index.html")

TEMPLATES[0]['DIRS'] += (os.path.join(BASE_DIR, "templates"),)

DEBUG = True
