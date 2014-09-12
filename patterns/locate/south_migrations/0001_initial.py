# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from wq.db.patterns.locate.models import SRID


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Location'
        db.create_table('wq_location', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('is_primary', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.GeometryField')(srid=SRID)),
            ('accuracy', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('locate', ['Location'])

        # Create index
        db.execute("""CREATE INDEX wq_location_idx ON wq_location
                         (content_type_id, object_id)""")

    def backwards(self, orm):

        # Drop index
        db.execute("DROP INDEX wq_location_idx;")

        # Deleting model 'Location'
        db.delete_table('wq_location')

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locate.location': {
            'Meta': {'object_name': 'Location', 'db_table': "'wq_location'"},
            'accuracy': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {'srid': SRID}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_primary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['locate']
