from __future__ import absolute_import

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', "tests.settings")

from django.test.utils import setup_test_environment
setup_test_environment()

import django
django.setup()

from django.core.management import call_command
# Migrate auth first since some unmigrated test apps depend on it...
call_command('migrate', 'auth', interactive=False)
call_command('migrate', interactive=False)
