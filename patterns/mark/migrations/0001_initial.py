# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import swapper


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        swapper.dependency('mark', 'MarkdownType'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkdownType',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'swappable': swapper.swappable_setting('mark', 'MarkdownType'),
                'db_table': 'wq_markdowntype',
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
                ('type', models.ForeignKey(to=swapper.get_model_name('mark', 'MarkdownType'))),
            ],
            options={
                'db_table': 'wq_markdown',
            },
            bases=(models.Model,),
        ),
    ]
