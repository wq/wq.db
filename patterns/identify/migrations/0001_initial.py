# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Authority',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('homepage', models.URLField(null=True, blank=True)),
                ('object_url', models.URLField(null=True, blank=True)),
            ],
            options={
                'db_table': 'wq_identifiertype',
                'verbose_name_plural': 'authorities',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('slug', models.SlugField(blank=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('object_id', models.PositiveIntegerField()),
                ('authority', models.ForeignKey(null=True, to='identify.Authority', blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'db_table': 'wq_identifier',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PrimaryIdentifier',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('identify.identifier',),
        ),
    ]
