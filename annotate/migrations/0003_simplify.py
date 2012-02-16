# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'AnnotationQualifier'
        db.delete_table('annotate_annotationqualifier')

        # Removing M2M table for field types on 'AnnotationQualifier'
        db.delete_table('annotate_annotationqualifier_types')

        # Deleting field 'Annotation.qualifier'
        db.delete_column('annotate_annotation', 'qualifier_id')

        # Adding field 'AnnotationType.contenttype'
        db.add_column('annotate_annotationtype', 'contenttype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True), keep_default=False)

        # Removing M2M table for field models on 'AnnotationType'
        db.delete_table('annotate_annotationtype_models')


    def backwards(self, orm):
        
        # Adding model 'AnnotationQualifier'
        db.create_table('annotate_annotationqualifier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('annotate', ['AnnotationQualifier'])

        # Adding M2M table for field types on 'AnnotationQualifier'
        db.create_table('annotate_annotationqualifier_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('annotationqualifier', models.ForeignKey(orm['annotate.annotationqualifier'], null=False)),
            ('annotationtype', models.ForeignKey(orm['annotate.annotationtype'], null=False))
        ))
        db.create_unique('annotate_annotationqualifier_types', ['annotationqualifier_id', 'annotationtype_id'])

        # Adding field 'Annotation.qualifier'
        db.add_column('annotate_annotation', 'qualifier', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotate.AnnotationQualifier'], null=True, blank=True), keep_default=False)

        # Deleting field 'AnnotationType.contenttype'
        db.delete_column('annotate_annotationtype', 'contenttype_id')

        # Adding M2M table for field models on 'AnnotationType'
        db.create_table('annotate_annotationtype_models', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('annotationtype', models.ForeignKey(orm['annotate.annotationtype'], null=False)),
            ('contenttype', models.ForeignKey(orm['contenttypes.contenttype'], null=False))
        ))
        db.create_unique('annotate_annotationtype_models', ['annotationtype_id', 'contenttype_id'])


    models = {
        'annotate.annotation': {
            'Meta': {'object_name': 'Annotation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotate.AnnotationType']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'annotate.annotationtype': {
            'Meta': {'object_name': 'AnnotationType'},
            'contenttype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['annotate']
