import os


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": (
                "django.template.context_processors.csrf",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            )
        },
    }
]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "wq.db.rest.renderers.HTMLRenderer",
        "wq.db.rest.renderers.JSONRenderer",
        "wq.db.rest.renderers.GeoJSONRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "wq.db.rest.pagination.Pagination",
    "PAGE_SIZE": 50,
    "DEFAULT_PERMISSION_CLASSES": ("wq.db.rest.permissions.ModelPermissions",),
    "DEFAULT_FILTER_BACKENDS": ("wq.db.rest.filters.FilterBackend",),
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "wq.db.rest.negotiation.ContentNegotiation",
}

SECRET_KEY = "1234"

MIDDLEWARE_CLASSES = ("django.middleware.csrf.CsrfViewMiddleware",)

INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "wq.db.rest",
    "wq.db.rest.auth",
    "tests.rest_app",
    "tests.conflict_app",
    "tests.patterns_app",
    "tests.naturalkey_app",
)

VARIANT = os.environ.get("TEST_VARIANT")

if VARIANT in ("postgis", "spatialite"):
    WITH_GIS = True
else:
    WITH_GIS = False

if VARIANT == "nonroot":
    WITH_NONROOT = True
else:
    WITH_NONROOT = False

if WITH_GIS:
    INSTALLED_APPS += ("tests.gis_app",)


if VARIANT in ("postgis", "postgres"):
    if WITH_GIS:
        engine = "django.contrib.gis.db.backends.postgis"
    else:
        engine = "django.db.backends.postgresql"
    DATABASES = {
        "default": {
            "ENGINE": engine,
            "NAME": "wqdb_test",
            "USER": os.environ.get("USER"),
        }
    }
else:
    if WITH_GIS:
        engine = "django.contrib.gis.db.backends.spatialite"
        SPATIALITE_LIBRARY_PATH = "mod_spatialite.so"
    else:
        engine = "django.db.backends.sqlite3"
    DATABASES = {
        "default": {
            "ENGINE": engine,
            "NAME": "wqdb_test.sqlite3",
        }
    }

USE_TZ = True
TIME_ZONE = "America/Chicago"

ROOT_URLCONF = "tests.urls"
BASE_DIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
VERSION_TXT = os.path.join(BASE_DIR, "version.txt")
WQ_APP_TEMPLATE = os.path.join(BASE_DIR, "index.html")

DEBUG = True
