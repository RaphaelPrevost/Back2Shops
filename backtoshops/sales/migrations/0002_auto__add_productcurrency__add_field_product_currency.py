# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ProductCurrency'
        db.create_table('sales_productcurrency', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('is_default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('sales', ['ProductCurrency'])

        # Adding field 'Product.currency'
        db.add_column('sales_product', 'currency', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['sales.ProductCurrency']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'ProductCurrency'
        db.delete_table('sales_productcurrency')

        # Deleting field 'Product.currency'
        db.delete_column('sales_product', 'currency_id')


    models = {
        'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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
            'shops': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['shops.Shop']", 'null': 'True', 'blank': 'True'}),
            'total_rest_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type_stock': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'})
        },
        'shops.shop': {
            'Meta': {'object_name': 'Shop'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'catcher': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
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
