# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Shipping'
        db.create_table(u'orders_shipping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('addr_orig', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('addr_dest', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('carrier', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.Carrier'], null=True, blank=True)),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.Service'], null=True, blank=True)),
            ('handling_fee', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('ship_and_handling_fee', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('total_fee', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'orders', ['Shipping'])


    def backwards(self, orm):
        # Deleting model 'Shipping'
        db.delete_table(u'orders_shipping')


    models = {
        u'orders.shipping': {
            'Meta': {'object_name': 'Shipping'},
            'addr_dest': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'addr_orig': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Carrier']", 'null': 'True', 'blank': 'True'}),
            'handling_fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Service']", 'null': 'True', 'blank': 'True'}),
            'ship_and_handling_fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'total_fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
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

    complete_apps = ['orders']