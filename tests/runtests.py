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
            'wq.db.rest',
            'wq.db.rest.auth',
            'wq.db.patterns.identify',
            'tests.testapp',
        ),
        **wqdb_settings
    )

    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    result = test_runner.run_tests((
        'wq.db.rest',
        'tests.testapp',
    ))
    sys.exit(result)

if __name__ == "__main__":
    main()
