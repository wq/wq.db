# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields

from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, blank=True, null=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(srid=settings.SRID)),
                ('accuracy', models.IntegerField(blank=True, null=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'db_table': 'wq_location',
            },
            bases=(models.Model,),
        ),
    ]
