# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'AnnotatedModel'
        db.create_table('annotate_annotatedmodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('annotate', ['AnnotatedModel'])

        # Adding model 'AnnotationType'
        db.create_table('annotate_annotationtype', (
            ('identifiedmodel_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['identify.IdentifiedModel'], unique=True, primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('annotate', ['AnnotationType'])

        # Adding M2M table for field models on 'AnnotationType'
        db.create_table('annotate_annotationtype_models', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('annotationtype', models.ForeignKey(orm['annotate.annotationtype'], null=False)),
            ('contenttype', models.ForeignKey(orm['contenttypes.contenttype'], null=False))
        ))
        db.create_unique('annotate_annotationtype_models', ['annotationtype_id', 'contenttype_id'])

        # Adding model 'Annotation'
        db.create_table('annotate_annotation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotate.AnnotationType'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('annotate', ['Annotation'])


    def backwards(self, orm):
        
        # Deleting model 'AnnotatedModel'
        db.delete_table('annotate_annotatedmodel')

        # Deleting model 'AnnotationType'
        db.delete_table('annotate_annotationtype')

        # Removing M2M table for field models on 'AnnotationType'
        db.delete_table('annotate_annotationtype_models')

        # Deleting model 'Annotation'
        db.delete_table('annotate_annotation')


    models = {
        'annotate.annotatedmodel': {
            'Meta': {'object_name': 'AnnotatedModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'annotate.annotation': {
            'Meta': {'object_name': 'Annotation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotate.AnnotationType']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'annotate.annotationtype': {
            'Meta': {'object_name': 'AnnotationType', '_ormbases': ['identify.IdentifiedModel']},
            'description': ('django.db.models.fields.TextField', [], {}),
            'identifiedmodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['identify.IdentifiedModel']", 'unique': 'True', 'primary_key': 'True'}),
            'models': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['contenttypes.ContentType']", 'symmetrical': 'False'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'identify.authority': {
            'Meta': {'object_name': 'Authority'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'identify.identifiedmodel': {
            'Meta': {'object_name': 'IdentifiedModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'identify.identifier': {
            'Meta': {'object_name': 'Identifier'},
            'authority': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['identify.Authority']", 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_primary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'valid_from': ('django.db.models.fields.DateField', [], {'blank': 'True'}),
            'valid_to': ('django.db.models.fields.DateField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['annotate']
