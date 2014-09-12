# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import wq.db.contrib.files.models

import swapper


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255, blank=True, null=True)),
                ('file', wq.db.contrib.files.models.FileField(upload_to='.', height_field='height', width_field='width')),
                ('size', models.IntegerField(blank=True, null=True)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'swappable': swapper.swappable_setting('files', 'File'),
                'db_table': 'wq_file',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('mimetype', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'wq_filetype',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='file',
            name='type',
            field=models.ForeignKey(to='files.FileType', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True),
            preserve_default=True,
        ),
    ]
