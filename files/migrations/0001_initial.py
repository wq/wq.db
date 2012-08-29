# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'FileType'
        db.create_table('wq_filetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('mimetype', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('files', ['FileType'])

        # Adding model 'BaseFile'
        db.create_table('wq_basefile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['files.FileType'], null=True, blank=True)),
            ('annotations', self.gf('wq.db.annotate.models.AnnotationSet')(to=orm['annotate.Annotation'])),
        ))
        db.send_create_signal('files', ['BaseFile'])

        # Adding model 'File'
        db.create_table('wq_file', (
            ('basefile_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['files.BaseFile'], unique=True, primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('files', ['File'])

        # Adding model 'Image'
        db.create_table('wq_image', (
            ('basefile_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['files.BaseFile'], unique=True, primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('files', ['Image'])


    def backwards(self, orm):
        
        # Deleting model 'FileType'
        db.delete_table('wq_filetype')

        # Deleting model 'BaseFile'
        db.delete_table('wq_basefile')

        # Deleting model 'File'
        db.delete_table('wq_file')

        # Deleting model 'Image'
        db.delete_table('wq_image')


    models = {
        'annotate.annotation': {
            'Meta': {'object_name': 'Annotation', 'db_table': "'wq_annotation'"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotate.AnnotationType']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
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
        },
        'files.basefile': {
            'Meta': {'object_name': 'BaseFile', 'db_table': "'wq_basefile'"},
            'annotations': ('wq.db.annotate.models.AnnotationSet', [], {'to': "orm['annotate.Annotation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['files.FileType']", 'null': 'True', 'blank': 'True'})
        },
        'files.file': {
            'Meta': {'object_name': 'File', 'db_table': "'wq_file'", '_ormbases': ['files.BaseFile']},
            'basefile_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['files.BaseFile']", 'unique': 'True', 'primary_key': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'files.filetype': {
            'Meta': {'object_name': 'FileType', 'db_table': "'wq_filetype'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'files.image': {
            'Meta': {'object_name': 'Image', 'db_table': "'wq_image'", '_ormbases': ['files.BaseFile']},
            'basefile_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['files.BaseFile']", 'unique': 'True', 'primary_key': 'True'}),
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'relate.inverserelationship': {
            'Meta': {'object_name': 'InverseRelationship', 'db_table': "'wq_relationship'", '_ormbases': ['relate.Relationship'], 'proxy': 'True'}
        },
        'relate.relationship': {
            'Meta': {'object_name': 'Relationship', 'db_table': "'wq_relationship'"},
            'from_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'from_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'to_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['relate.RelationshipType']"})
        },
        'relate.relationshiptype': {
            'Meta': {'object_name': 'RelationshipType', 'db_table': "'wq_relationshiptype'"},
            'from_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inverse_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'to_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"})
        }
    }

    complete_apps = ['files']
