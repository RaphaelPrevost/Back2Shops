# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ShippingCarrierService'
        db.create_table(u'sales_shippingcarrierservice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sale', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.Sale'])),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.Service'])),
        ))
        db.send_create_signal(u'sales', ['ShippingCarrierService'])

        # Adding model 'Shipping'
        db.create_table(u'sales_shipping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sale', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['sales.Sale'], unique=True, null=True, blank=True)),
            ('handling_fee', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('allow_group_shipment', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('allow_pickup', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('pickup_voids_handling_fee', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('shipping_calculation', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'sales', ['Shipping'])

        # Adding model 'ShippingCustomRule'
        db.create_table(u'sales_shippingcustomrule', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sale', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.Sale'])),
            ('custom_shipping_rate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shippings.CustomShippingRate'])),
        ))
        db.send_create_signal(u'sales', ['ShippingCustomRule'])


    def backwards(self, orm):
        # Deleting model 'ShippingCarrierService'
        db.delete_table(u'sales_shippingcarrierservice')

        # Deleting model 'Shipping'
        db.delete_table(u'sales_shipping')

        # Deleting model 'ShippingCustomRule'
        db.delete_table(u'sales_shippingcustomrule')


    models = {
        u'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'attributes.commonattribute': {
            'Meta': {'object_name': 'CommonAttribute'},
            'for_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'common_attributes'", 'to': u"orm['sales.ProductType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'sales.product': {
            'Meta': {'object_name': 'Product'},
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['sales.ProductBrand']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['sales.ProductCategory']"}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.ProductCurrency']"}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'discount': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'discount_price': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'discount_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'normal_price': ('django.db.models.fields.FloatField', [], {}),
            'sale': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sales.Sale']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['sales.ProductType']"}),
            'valid_from': ('django.db.models.fields.DateField', [], {}),
            'valid_to': ('django.db.models.fields.DateField', [], {'null': 'True'})
        },
        u'sales.productbrand': {
            'Meta': {'object_name': 'ProductBrand'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'default': "'NULL'", 'max_length': '100'}),
            'seller': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sold_brands'", 'to': u"orm['accounts.Brand']"})
        },
        u'sales.productcategory': {
            'Meta': {'object_name': 'ProductCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'sales.productcurrency': {
            'Meta': {'object_name': 'ProductCurrency'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'sales.productpicture': {
            'Meta': {'object_name': 'ProductPicture'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_brand_attribute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'pictures'", 'null': 'True', 'to': u"orm['sales.Product']"})
        },
        u'sales.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.ProductCategory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'sales.sale': {
            'Meta': {'object_name': 'Sale'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'direct_sale': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sales'", 'on_delete': 'models.DO_NOTHING', 'to': u"orm['accounts.Brand']"}),
            'shops': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['shops.Shop']", 'null': 'True', 'through': u"orm['sales.ShopsInSale']", 'blank': 'True'}),
            'total_rest_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type_stock': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'})
        },
        u'sales.shipping': {
            'Meta': {'object_name': 'Shipping'},
            'allow_group_shipment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allow_pickup': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'handling_fee': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pickup_voids_handling_fee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sale': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sales.Sale']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'shipping_calculation': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'sales.shippingcarrierservice': {
            'Meta': {'object_name': 'ShippingCarrierService'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sale': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.Sale']"}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Service']"})
        },
        u'sales.shippingcustomrule': {
            'Meta': {'object_name': 'ShippingCustomRule'},
            'custom_shipping_rate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.CustomShippingRate']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sale': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.Sale']"})
        },
        u'sales.shopsinsale': {
            'Meta': {'object_name': 'ShopsInSale'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_freezed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sale': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.Sale']"}),
            'shop': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shops.Shop']"})
        },
        u'sales.typeattributeprice': {
            'Meta': {'object_name': 'TypeAttributePrice'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sale': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.Sale']"}),
            'type_attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['attributes.CommonAttribute']"}),
            'type_attribute_price': ('django.db.models.fields.FloatField', [], {})
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
        u'shippings.service': {
            'Meta': {'object_name': 'Service'},
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'services'", 'to': u"orm['shippings.Carrier']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shops.shop': {
            'Meta': {'object_name': 'Shop'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'catcher': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['countries.Country']", 'null': 'True', 'blank': 'True'}),
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
            'upc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sales']