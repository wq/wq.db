import sys
import os
import django
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
        MEDIA_ROOT=os.path.join(os.path.dirname(__file__), "media"),
        ROOT_URLCONF="tests.urls",
        CELERY_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND='redis://localhost/0',
        INSTALLED_APPS=(
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'wq.db.rest',
            'wq.db.rest.auth',
            'wq.db.patterns.identify',
            'wq.db.patterns.annotate',
            'wq.db.patterns.relate',
            'wq.db.contrib.vera',
            'wq.db.contrib.files',
            'wq.db.contrib.dbio',
            'tests.rest_app',
            'tests.patterns_app',
            'tests.rest_app',
        ),
        **wqdb_settings
    )

    # Django >= 1.7
    if hasattr(django, 'setup'):
        django.setup()

    # Tests for default model implementations
    from django.test.utils import get_runner
    from .celery import app as celery_app
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    test_runner.setup_test_environment()
    suite = test_runner.build_suite((
        'tests.rest_app',
        'tests.patterns_app',
        'tests.vera_app',
    ), None)
    old_config = test_runner.setup_databases()
    result = test_runner.run_suite(suite)
    count = test_runner.suite_result(suite, result)

    # Tests on swapped model implementations
    from django.test.utils import override_settings
    from django.core.management import call_command
    override = override_settings(
        INSTALLED_APPS=settings.INSTALLED_APPS + ("tests.swap_app",),
        WQ_SITE_MODEL="swap_app.Site",
        WQ_REPORT_MODEL="swap_app.Report",
        WQ_DEFAULT_REPORT_STATUS=100,
    )
    override.enable()
    reset_vera()
    call_command("syncdb", interactive=False, traceback=False)

    suite = test_runner.build_suite((
        'tests.swap_app',
    ))
    result = test_runner.run_suite(suite)
    count += test_runner.suite_result(suite, result)
    test_runner.teardown_databases(old_config)
    test_runner.teardown_test_environment()

    sys.exit(count)


def reset_vera():
    """
    Hack to reset vera app so that swapped models can be tested
    """
    from django.db.models.loading import AppCache
    from wq.db.contrib.vera import models as vera
    cache = AppCache()
    cache._get_models_cache.clear()
    del cache.app_models['vera']
    reload(vera)
    cache.loaded = False
    # Refresh dbio's references to vera models
    from wq.db.contrib.dbio import tasks as dbtasks
    reload(dbtasks)


if __name__ == "__main__":
    main()
