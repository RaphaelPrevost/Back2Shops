# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'ProductPicture.content_type'
        db.alter_column('pictures_productpicture', 'content_type_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True))

        # Changing field 'ProductPicture.object_id'
        db.alter_column('pictures_productpicture', 'object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))


    def backwards(self, orm):
        
        # Changing field 'ProductPicture.content_type'
        db.alter_column('pictures_productpicture', 'content_type_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['contenttypes.ContentType']))

        # Changing field 'ProductPicture.object_id'
        db.alter_column('pictures_productpicture', 'object_id', self.gf('django.db.models.fields.PositiveIntegerField')(default=1))


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pictures.productpicture': {
            'Meta': {'object_name': 'ProductPicture'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['pictures']
