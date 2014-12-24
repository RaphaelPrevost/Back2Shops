# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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
        
        # Adding model 'ShopsInSale'
        db.create_table('sales_shopsinsale', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sale', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.Sale'])),
            ('shop', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shops.Shop'])),
            ('is_freezed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('sales', ['ShopsInSale'])

        # Removing M2M table for field shops on 'Sale'
        db.delete_table('sales_sale_shops')


    def backwards(self, orm):
        
        # Deleting model 'ShopsInSale'
        db.delete_table('sales_shopsinsale')

        # Adding M2M table for field shops on 'Sale'
        db.create_table('sales_sale_shops', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sale', models.ForeignKey(orm['sales.sale'], null=False)),
            ('shop', models.ForeignKey(orm['shops.shop'], null=False))
        ))
        db.create_unique('sales_sale_shops', ['sale_id', 'shop_id'])


    models = {
        'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'sales.product': {
            'Meta': {'object_name': 'Product'},
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['sales.ProductBrand']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['sales.ProductCategory']"}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sales.ProductCurrency']"}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '500'}),
            'discount': ('django.db.models.fields.FloatField', [], {}),
            'discount_price': ('django.db.models.fields.FloatField', [], {}),
            'discount_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'normal_price': ('django.db.models.fields.FloatField', [], {}),
            'sale': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['sales.Sale']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['sales.ProductType']"}),
            'valid_from': ('django.db.models.fields.DateField', [], {}),
            'valid_to': ('django.db.models.fields.DateField', [], {})
        },
        'sales.productbrand': {
            'Meta': {'object_name': 'ProductBrand'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'default': "'NULL'", 'max_length': '100'}),
            'seller': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sold_brands'", 'to': "orm['accounts.Brand']"})
        },
        'sales.productcategory': {
            'Meta': {'object_name': 'ProductCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'sales.productcurrency': {
            'Meta': {'object_name': 'ProductCurrency'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'sales.productpicture': {
            'Meta': {'object_name': 'ProductPicture'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_brand_attribute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'pictures'", 'null': 'True', 'to': "orm['sales.Product']"})
        },
        'sales.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sales.ProductCategory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'sales.sale': {
            'Meta': {'object_name': 'Sale'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'direct_sale': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sales'", 'to': "orm['accounts.Brand']"}),
            'shops': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['shops.Shop']", 'null': 'True', 'through': "orm['sales.ShopsInSale']", 'blank': 'True'}),
            'total_rest_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type_stock': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'})
        },
        'sales.shopsinsale': {
            'Meta': {'object_name': 'ShopsInSale'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_freezed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sale': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sales.Sale']"}),
            'shop': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shops.Shop']"})
        },
        'shops.shop': {
            'Meta': {'object_name': 'Shop'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'catcher': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['countries.Country']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'gestion_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'shops'", 'to': "orm['accounts.Brand']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'opening_hours': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'upc': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sales']
