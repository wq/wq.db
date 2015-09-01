# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotate', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='annotationtype',
            name='contenttype',
        ),
    ]
