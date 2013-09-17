# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from wq.db.patterns.base import swapper


class Migration(SchemaMigration):

    def forwards(self, orm):

        if not swapper.is_swapped('annotate', 'AnnotationType'):

            # Adding model 'AnnotationType'
            db.create_table('wq_annotationtype', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('contenttype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ))
            db.send_create_signal('annotate', ['AnnotationType'])

        if not swapper.is_swapped('annotate', 'Annotation'):
            AnnotationType = swapper.load_model('annotate', 'AnnotationType', orm)

            # Adding model 'Annotation'
            db.create_table('wq_annotation', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),

                ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=AnnotationType)),
                ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
                ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ))
            db.send_create_signal('annotate', ['Annotation'])

            # Create index
            db.execute("""CREATE INDEX wq_annotation_idx ON wq_annotation
                             (content_type_id, object_id)""")

    def backwards(self, orm):

        if not swapper.is_swapped('annotate', 'AnnotationType'):
            # Deleting model 'AnnotationType'
            db.delete_table('wq_annotationtype')

        if not swapper.is_swapped('annotate', 'Annotation'):
            # Drop index
            db.execute("DROP INDEX wq_annotation_idx;")

            # Deleting model 'Annotation'
            db.delete_table('wq_annotation')

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
