# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Carrier'
        db.create_table(u'shippings_carrier', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('flag', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'shippings', ['Carrier'])

        # Adding model 'Service'
        db.create_table(u'shippings_service', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('carrier', self.gf('django.db.models.fields.related.ForeignKey')(related_name='services', to=orm['shippings.Carrier'])),
        ))
        db.send_create_signal(u'shippings', ['Service'])


    def backwards(self, orm):
        # Deleting model 'Carrier'
        db.delete_table(u'shippings_carrier')

        # Deleting model 'Service'
        db.delete_table(u'shippings_service')


    models = {
        u'shippings.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'flag': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shippings.service': {
            'Meta': {'object_name': 'Service'},
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'services'", 'to': u"orm['shippings.Carrier']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['shippings']