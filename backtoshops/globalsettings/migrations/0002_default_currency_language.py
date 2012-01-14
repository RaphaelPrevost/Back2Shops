# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'globalsettings.globalsettings': {
            'Meta': {'object_name': 'GlobalSettings'},
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['globalsettings']
