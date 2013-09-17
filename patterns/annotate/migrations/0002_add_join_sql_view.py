# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from wq.db.patterns.base import swapper


class Migration(DataMigration):

    def forwards(self, orm):
        if swapper.is_swapped('annotate', 'AnnotationType'):
            return

        if swapper.is_swapped('annotate', 'Annotation'):
            return

        if db.backend_name != 'postgres':
            print "Warning: Non-postgres database detected; convenience view will not be created."
            return

        db.execute('''
CREATE OR REPLACE VIEW wq_annotation_joined AS
SELECT ct.app_label, ct.model, a.object_id, at.id AS type_id, at.name AS type_name, a.value
FROM wq_annotation a
JOIN wq_annotationtype at ON at.id = a.type_id
JOIN django_content_type ct ON a.content_type_id = ct.id;''')

    def backwards(self, orm):
        if swapper.is_swapped('annotate', 'AnnotationType'):
            return
        if swapper.is_swapped('annotate', 'Annotation'):
            return
        if db.backend_name != 'postgres':
            return
        db.execute("DROP VIEW wq_annotation_joined;")

    models = {
        'annotate.annotation': {
            'Meta': {'object_name': 'Annotation', 'db_table': "'wq_annotation'"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotate.AnnotationType']"}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'annotate.annotationtype': {
            'Meta': {'object_name': 'AnnotationType', 'db_table': "'wq_annotationtype'"},
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
