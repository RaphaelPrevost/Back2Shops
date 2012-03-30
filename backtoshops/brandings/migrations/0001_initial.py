# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Branding'
        db.create_table('brandings_branding', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('sort_key', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('img', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('show_from', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('show_until', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('brandings', ['Branding'])


    def backwards(self, orm):
        
        # Deleting model 'Branding'
        db.delete_table('brandings_branding')


    models = {
        'brandings.branding': {
            'Meta': {'object_name': 'Branding'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'img': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'show_from': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'show_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sort_key': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        }
    }

    complete_apps = ['brandings']
