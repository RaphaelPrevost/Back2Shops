# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'GlobalSettings'
        db.create_table('globalsettings_globalsettings', (
            ('key', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('globalsettings', ['GlobalSettings'])


    def backwards(self, orm):
        
        # Deleting model 'GlobalSettings'
        db.delete_table('globalsettings_globalsettings')


    models = {
        'globalsettings.globalsettings': {
            'Meta': {'object_name': 'GlobalSettings'},
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['globalsettings']
