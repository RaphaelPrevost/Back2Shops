# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Renaming field 'Rate.taxable'
        db.rename_column(u'taxes_rate', 'taxable', 'applies_to_delivery')

        # Adding field 'Rate.applies_after_promos'
        db.add_column(u'taxes_rate', 'applies_after_promos',
                      self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Rate.applies_to_free_items'
        db.add_column(u'taxes_rate', 'applies_to_free_items',
                      self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Rate.applies_to_manufacturer_promos'
        db.add_column(u'taxes_rate', 'applies_to_manufacturer_promos',
                      self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Renaming field 'Rate.applies_to_delivery'
        db.rename_column(u'taxes_rate', 'applies_to_delivery', 'taxable')

        # Deleting field 'Rate.applies_after_promos'
        db.delete_column(u'taxes_rate', 'applies_after_promos')

        # Deleting field 'Rate.applies_to_free_items'
        db.delete_column(u'taxes_rate', 'applies_to_free_items')

        # Deleting field 'Rate.applies_to_manufacturer_promos'
        db.delete_column(u'taxes_rate', 'applies_to_manufacturer_promos')


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
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        u'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'sales.productcategory': {
            'Meta': {'object_name': 'ProductCategory'},
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.Brand']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'valid': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'taxes.rate': {
            'Meta': {'object_name': 'Rate'},
            'applies_after_promos': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'applies_to': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.ProductCategory']", 'null': 'True', 'blank': 'True'}),
            'applies_to_business_accounts': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'applies_to_delivery': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'applies_to_free_items': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'applies_to_manufacturer_promos': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'applies_to_personal_accounts': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'apply_after': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display_on_front': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'rate': ('django.db.models.fields.FloatField', [], {}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'region'", 'to': u"orm['countries.Country']"}),
            'shipping_to_province': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'shipping_to_region': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shipping_to_region'", 'null': 'True', 'to': u"orm['countries.Country']"})
        }
    }

    complete_apps = ['taxes']
