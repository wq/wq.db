# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('from_object_id', models.PositiveIntegerField()),
                ('to_object_id', models.PositiveIntegerField()),
                ('computed', models.BooleanField(default=False)),
                ('from_content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='+')),
                ('to_content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='+')),
            ],
            options={
                'db_table': 'wq_relationship',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RelationshipType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255)),
                ('inverse_name', models.CharField(blank=True, null=True, max_length=255)),
                ('computed', models.BooleanField(default=False)),
                ('from_type', models.ForeignKey(to='contenttypes.ContentType', related_name='+')),
                ('to_type', models.ForeignKey(to='contenttypes.ContentType', related_name='+')),
            ],
            options={
                'db_table': 'wq_relationshiptype',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='relationship',
            name='type',
            field=models.ForeignKey(to='relate.RelationshipType'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='InverseRelationship',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('relate.relationship',),
        ),
        migrations.CreateModel(
            name='InverseRelationshipType',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('relate.relationshiptype',),
        ),
    ]
