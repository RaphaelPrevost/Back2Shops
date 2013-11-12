# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Shipping.order'
        db.delete_column(u'orders_shipping', 'order')

        # Adding field 'Shipping.shipment'
        db.add_column(u'orders_shipping', 'shipment',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Shipping.order'
        raise RuntimeError("Cannot reverse this migration. 'Shipping.order' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Shipping.order'
        db.add_column(u'orders_shipping', 'order',
                      self.gf('django.db.models.fields.IntegerField')(),
                      keep_default=False)

        # Deleting field 'Shipping.shipment'
        db.delete_column(u'orders_shipping', 'shipment')


    models = {
        u'orders.shipping': {
            'Meta': {'object_name': 'Shipping'},
            'addr_dest': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'addr_orig': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Carrier']", 'null': 'True', 'blank': 'True'}),
            'handling_fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Service']", 'null': 'True', 'blank': 'True'}),
            'ship_and_handling_fee': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'shipment': ('django.db.models.fields.IntegerField', [], {}),
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