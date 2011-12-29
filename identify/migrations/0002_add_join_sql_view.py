# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        db.execute('''
CREATE OR REPLACE VIEW identify_identifier_joined AS 
SELECT ct.app_label, ct.model, i.object_id, i.name AS identifier
FROM identify_identifier i
JOIN django_content_type ct ON i.content_type_id = ct.id;''')

    def backwards(self, orm):
        db.execute("DROP VIEW identify_identifier_joined;");


    models = {
        'annotate.annotation': {
            'Meta': {'object_name': 'Annotation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'qualifier': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotate.AnnotationQualifier']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotate.AnnotationType']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'annotate.annotationqualifier': {
            'Meta': {'object_name': 'AnnotationQualifier'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['annotate.AnnotationType']", 'symmetrical': 'False'})
        },
        'annotate.annotationtype': {
            'Meta': {'object_name': 'AnnotationType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'models': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['contenttypes.ContentType']", 'symmetrical': 'False'}),
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
