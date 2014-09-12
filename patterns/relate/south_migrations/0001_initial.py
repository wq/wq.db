# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Relationship'
        db.create_table('wq_relationship', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['relate.RelationshipType'])),
            ('from_content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['contenttypes.ContentType'])),
            ('from_object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('to_content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['contenttypes.ContentType'])),
            ('to_object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('computed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('relate', ['Relationship'])

        # Adding model 'RelationshipType'
        db.create_table('wq_relationshiptype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('inverse_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('from_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['contenttypes.ContentType'])),
            ('to_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['contenttypes.ContentType'])),
            ('computed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('relate', ['RelationshipType'])

        # Create indexes
        db.execute("""CREATE INDEX wq_relationship_from_idx ON wq_relationship
                         (from_content_type_id, from_object_id)""")
        db.execute("""CREATE INDEX wq_relationship_to_idx ON wq_relationship
                         (to_content_type_id, to_object_id)""")

    def backwards(self, orm):

        # Drop indexes
        db.execute("DROP INDEX wq_relationship_to_idx")
        db.execute("DROP INDEX wq_relationship_from_idx")

        # Deleting model 'Relationship'
        db.delete_table('wq_relationship')

        # Deleting model 'RelationshipType'
        db.delete_table('wq_relationshiptype')

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'relate.relationship': {
            'Meta': {'object_name': 'Relationship', 'db_table': "'wq_relationship'"},
            'computed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'from_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'from_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'to_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['relate.RelationshipType']"})
        },
        'relate.relationshiptype': {
            'Meta': {'object_name': 'RelationshipType', 'db_table': "'wq_relationshiptype'"},
            'computed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'from_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inverse_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'to_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"})
        }
    }

    complete_apps = ['relate']
