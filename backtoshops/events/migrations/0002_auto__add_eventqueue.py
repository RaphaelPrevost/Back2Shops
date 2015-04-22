# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EventQueue'
        db.create_table(u'events_eventqueue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['events.Event'])),
            ('param_values', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('handled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('error', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'events', ['EventQueue'])


    def backwards(self, orm):
        # Deleting model 'EventQueue'
        db.delete_table(u'events_eventqueue')


    models = {
        u'events.event': {
            'Meta': {'object_name': 'Event'},
            'desc': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'handler_is_private': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'handler_method': ('django.db.models.fields.CharField', [], {'default': "'post'", 'max_length': '10', 'blank': 'True'}),
            'handler_url': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'events.eventhandlerparam': {
            'Meta': {'object_name': 'EventHandlerParam'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'event_handler_params'", 'to': u"orm['events.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        u'events.eventqueue': {
            'Meta': {'object_name': 'EventQueue'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['events.Event']"}),
            'handled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'param_values': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['events']