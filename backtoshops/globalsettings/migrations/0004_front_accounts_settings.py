# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.core.management import call_command

class Migration(DataMigration):

    def forwards(self, orm):
        call_command("loaddata", "globalsettings/front_accounts_settings.json")

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'globalsettings.globalsettings': {
            'Meta': {'object_name': 'GlobalSettings'},
            'key': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['globalsettings']
    symmetrical = True
