# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CustomShippingRate'
        db.create_table(u'shippings_customshippingrate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seller', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Brand'])),
            ('shipment_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('total_order_type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('total_order_upper', self.gf('django.db.models.fields.FloatField')()),
            ('total_order_lower', self.gf('django.db.models.fields.FloatField')()),
            ('shipping_rate', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'shippings', ['CustomShippingRate'])

        # Adding model 'CustomShippingRateInShipping'
        db.create_table(u'shippings_customshippingrateinshipping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shipping', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.Shipping'])),
            ('custom_shipping_rate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.CustomShippingRate'])),
        ))
        db.send_create_signal(u'shippings', ['CustomShippingRateInShipping'])

        # Adding model 'Shipping'
        db.create_table(u'shippings_shipping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('handling_fee', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('allow_group_shipment', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('allow_pickup', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('pickup_voids_handling_fee', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('shipping_calculation', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'shippings', ['Shipping'])

        # Adding model 'ServiceInShipping'
        db.create_table(u'shippings_serviceinshipping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shipping', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.Shipping'])),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.Service'])),
        ))
        db.send_create_signal(u'shippings', ['ServiceInShipping'])


    def backwards(self, orm):
        # Deleting model 'CustomShippingRate'
        db.delete_table(u'shippings_customshippingrate')

        # Deleting model 'CustomShippingRateInShipping'
        db.delete_table(u'shippings_customshippingrateinshipping')

        # Deleting model 'Shipping'
        db.delete_table(u'shippings_shipping')

        # Deleting model 'ServiceInShipping'
        db.delete_table(u'shippings_serviceinshipping')


    models = {
        u'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shippings.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'flag': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shippings.customshippingrate': {
            'Meta': {'object_name': 'CustomShippingRate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seller': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.Brand']"}),
            'shipment_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'shipping_rate': ('django.db.models.fields.FloatField', [], {}),
            'total_order_lower': ('django.db.models.fields.FloatField', [], {}),
            'total_order_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'total_order_upper': ('django.db.models.fields.FloatField', [], {})
        },
        u'shippings.customshippingrateinshipping': {
            'Meta': {'object_name': 'CustomShippingRateInShipping'},
            'custom_shipping_rate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.CustomShippingRate']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shipping': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Shipping']"})
        },
        u'shippings.service': {
            'Meta': {'object_name': 'Service'},
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'services'", 'to': u"orm['shippings.Carrier']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shippings.serviceinshipping': {
            'Meta': {'object_name': 'ServiceInShipping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Service']"}),
            'shipping': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Shipping']"})
        },
        u'shippings.shipping': {
            'Meta': {'object_name': 'Shipping'},
            'allow_group_shipment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allow_pickup': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'handling_fee': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pickup_voids_handling_fee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shipping_calculation': ('django.db.models.fields.SmallIntegerField', [], {})
        }
    }

    complete_apps = ['shippings']