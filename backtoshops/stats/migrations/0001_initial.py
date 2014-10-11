# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Visitors'
        db.create_table(u'stats_visitors', (
            ('sid', self.gf('django.db.models.fields.CharField')(max_length=36, primary_key=True)),
            ('users_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('visit_time', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'stats', ['Visitors'])


    def backwards(self, orm):
        # Deleting model 'Visitors'
        db.delete_table(u'stats_visitors')


    models = {
        u'stats.visitors': {
            'Meta': {'object_name': 'Visitors'},
            'sid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'}),
            'users_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'visit_time': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['stats']