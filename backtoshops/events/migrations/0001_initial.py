# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Event'
        db.create_table(u'events_event', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('desc', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('handler_url', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('handler_method', self.gf('django.db.models.fields.CharField')(default='post', max_length=10, blank=True)),
            ('handler_is_private', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'events', ['Event'])

        # Adding model 'EventHandlerParam'
        db.create_table(u'events_eventhandlerparam', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='event_handler_params', to=orm['events.Event'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
        ))
        db.send_create_signal(u'events', ['EventHandlerParam'])


    def backwards(self, orm):
        # Deleting model 'Event'
        db.delete_table(u'events_event')

        # Deleting model 'EventHandlerParam'
        db.delete_table(u'events_eventhandlerparam')


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
        }
    }

    complete_apps = ['events']