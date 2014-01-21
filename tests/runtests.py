import sys
from django.conf import settings
from wq.db.rest import settings as wqdb_settings

wqdb_settings = {
    setting: getattr(wqdb_settings, setting)
    for setting in dir(wqdb_settings)
    if not setting.startswith('__')
}


def main():
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.contrib.gis.db.backends.postgis',
                'NAME': 'wqdb_test',
                'USER': 'postgres',
            }
        },
        ROOT_URLCONF="tests.urls",
        INSTALLED_APPS=(
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'wq.db.rest',
            'wq.db.rest.auth',
            'wq.db.patterns.identify',
            'wq.db.patterns.annotate',
            'wq.db.patterns.relate',
            'wq.db.contrib.vera',
            'tests.rest_app',
            'tests.patterns_app',
            'tests.rest_app',
        ),
        **wqdb_settings
    )

    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    result = test_runner.run_tests((
        'tests.rest_app',
        'tests.patterns_app',
        'tests.vera_app',
    ))
    sys.exit(result)

if __name__ == "__main__":
    main()
