import os

SECRET_KEY = '1234'

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'social.apps.django_app.default',
    'wq.db.rest',
    'wq.db.rest.auth',
    'wq.db.patterns.identify',
    'wq.db.patterns.annotate',
    'wq.db.patterns.relate',
    'wq.db.patterns.mark',
    'wq.db.patterns.locate',
    'wq.db.contrib.files',
    'tests.rest_app',
    'tests.patterns_app',
    'tests.chart_app',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'wqdb_test',
        'USER': 'postgres',
    }
}

ROOT_URLCONF = "tests.urls"
BASE_DIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "templates"),
)
VERSION_TXT = os.path.join(BASE_DIR, "version.txt")

LANGUAGES = (
    ('en', 'English'),
    ('ko', 'Korean'),
)

from wq.db.rest.settings import *  # NOQA
