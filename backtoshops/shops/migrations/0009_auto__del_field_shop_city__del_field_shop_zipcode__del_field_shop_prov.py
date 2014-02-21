# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    depends_on = ( ("address", "0001_initial"), )

    def forwards(self, orm):
        # Deleting field 'Shop.city'
        db.delete_column(u'shops_shop', 'city')

        # Deleting field 'Shop.zipcode'
        db.delete_column(u'shops_shop', 'zipcode')

        # Deleting field 'Shop.province_code'
        db.delete_column(u'shops_shop', 'province_code')

        # Deleting field 'Shop.country'
        db.delete_column(u'shops_shop', 'country_id')

        # Deleting field 'Shop.address'
        db.delete_column(u'shops_shop', 'address')


        # Changing field 'Shop.address'
        db.add_column(u'shops_shop', 'address',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['address.Address'], unique=True))
        # Adding index on 'Shop', fields ['address']
        db.create_index(u'shops_shop', ['address_id'])

        # Adding unique constraint on 'Shop', fields ['address']
        db.create_unique(u'shops_shop', ['address_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Shop', fields ['address']
        db.delete_unique(u'shops_shop', ['address_id'])

        # Removing index on 'Shop', fields ['address']
        db.delete_index(u'shops_shop', ['address_id'])

        # Deleting field 'Shop.address_id'
        db.delete_column(u'shops_shop', ['address_id'])

        # Adding field 'Shop.city'
        db.add_column(u'shops_shop', 'city',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=100),
                      keep_default=False)

        # Adding field 'Shop.zipcode'
        db.add_column(u'shops_shop', 'zipcode',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Shop.province_code'
        db.add_column(u'shops_shop', 'province_code',
                      self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Shop.country'
        db.add_column(u'shops_shop', 'country',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['countries.Country'], null=True, blank=True),
                      keep_default=False)

        # Changing field 'Shop.address'
        db.add_column(u'shops_shop', 'address',
                      self.gf('django.db.models.fields.CharField')(max_length=250, null=True))

    models = {
        u'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['address.Address']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'address.address': {
            'Meta': {'object_name': 'Address'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['countries.Country']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'province_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'shippings.shipping': {
            'Meta': {'object_name': 'Shipping'},
            'allow_group_shipment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allow_pickup': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'handling_fee': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pickup_voids_handling_fee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shipping_calculation': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'shops.defaultshipping': {
            'Meta': {'object_name': 'DefaultShipping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shipping': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Shipping']"}),
            'shop': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shops.Shop']"})
        },
        u'shops.shop': {
            'Meta': {'object_name': 'Shop'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['address.Address']", 'unique': 'True'}),
            'catcher': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'gestion_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'shops'", 'to': u"orm['accounts.Brand']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'opening_hours': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'upc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['shops']