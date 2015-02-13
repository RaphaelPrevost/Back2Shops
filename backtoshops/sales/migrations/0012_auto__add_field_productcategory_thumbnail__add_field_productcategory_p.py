# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ProductCategory.thumbnail'
        db.add_column(u'sales_productcategory', 'thumbnail',
                      self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ProductCategory.picture'
        db.add_column(u'sales_productcategory', 'picture',
                      self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ProductCategory.thumbnail'
        db.delete_column(u'sales_productcategory', 'thumbnail')

        # Deleting field 'ProductCategory.picture'
        db.delete_column(u'sales_productcategory', 'picture')


    models = {
        u'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['address.Address']", 'unique': 'True'}),
            'business_reg_num': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'tax_reg_num': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'})
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
        u'attributes.commonattribute': {
            'Meta': {'object_name': 'CommonAttribute'},
            'for_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'common_attributes'", 'to': u"orm['sales.ProductType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'valid': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
            'discount_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'normal_price': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'sale': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sales.Sale']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'standard_weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': u"orm['sales.ProductType']"}),
            'valid_from': ('django.db.models.fields.DateField', [], {}),
            'valid_to': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'weight_unit': ('django.db.models.fields.related.ForeignKey', [], {'default': "'kg'", 'to': u"orm['sales.WeightUnit']"})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'valid': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'valid': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
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
        u'sales.shippinginsale': {
            'Meta': {'object_name': 'ShippingInSale'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sale': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['sales.Sale']", 'unique': 'True'}),
            'shipping': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['shippings.Shipping']", 'unique': 'True'})
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
        u'sales.typeattributeweight': {
            'Meta': {'object_name': 'TypeAttributeWeight'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sale': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.Sale']"}),
            'type_attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['attributes.CommonAttribute']"}),
            'type_attribute_weight': ('django.db.models.fields.FloatField', [], {})
        },
        u'sales.weightunit': {
            'Meta': {'object_name': 'WeightUnit'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'})
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
        u'shops.shop': {
            'Meta': {'object_name': 'Shop'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['address.Address']", 'unique': 'True'}),
            'business_reg_num': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'catcher': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'default_currency': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'gestion_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'shops'", 'to': u"orm['accounts.Brand']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'opening_hours': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'tax_reg_num': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'upc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sales']
