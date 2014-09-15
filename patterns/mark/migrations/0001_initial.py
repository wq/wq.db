# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkdownType',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'swappable': 'WQ_MARKDOWNTYPE_MODEL',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Markdown',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('markdown', models.TextField(blank=True, null=True)),
                ('summary', models.CharField(blank=True, max_length=255, null=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('type', models.ForeignKey(to=settings.WQ_MARKDOWNTYPE_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MarkedModel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
